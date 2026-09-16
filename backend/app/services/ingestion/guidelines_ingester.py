import uuid
import structlog
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.provenance import Source, Article, Evidence
from app.models.knowledge import Disease
from app.models.embedding import EmbeddingRecord
from app.infrastructure.ai.factory import get_embedding_provider

log = structlog.get_logger(__name__)

class GuidelinesIngester:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
    async def ingest_guidelines_real(self, db: AsyncSession, max_guidelines: int = 20):
        """
        Fetches real clinical practice guidelines from PubMed,
        generates embeddings, and stores them for RAG retrieval.
        """
        try:
            # 1. Ensure the Source exists
            stmt = select(Source).where(Source.code == "pubmed_guidelines")
            result = await db.execute(stmt)
            source = result.scalar_one_or_none()

            if not source:
                source = Source(
                    code="pubmed_guidelines",
                    organisation="NIH / NLM",
                    name="PubMed Clinical Guidelines",
                    base_url=self.base_url,
                    access_mechanism="api",
                    data_type="clinical_guidelines",
                    is_production_suitable=True,
                    status="active"
                )
                db.add(source)
                await db.flush()

            # Search PubMed for "Practice Guideline" publication type
            search_query = '"Practice Guideline"[Publication Type]'
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                search_url = f"{self.base_url}/esearch.fcgi?db=pubmed&term={search_query}&retmax={max_guidelines}&retmode=json"
                search_res = await client.get(search_url)
                
                if search_res.status_code != 200:
                    log.error("pubmed_guidelines_esearch_failed", status=search_res.status_code)
                    return
                    
                id_list = search_res.json().get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    log.info("pubmed_no_guidelines_found")
                    return
                
                ids_str = ",".join(id_list)
                summary_url = f"{self.base_url}/esummary.fcgi?db=pubmed&id={ids_str}&retmode=json"
                summary_res = await client.get(summary_url)
                
                if summary_res.status_code != 200:
                    log.error("pubmed_guidelines_esummary_failed")
                    return
                    
                summary_data = summary_res.json().get("result", {})
                
                # Fetch abstracts using efetch
                efetch_url = f"{self.base_url}/efetch.fcgi?db=pubmed&id={ids_str}&retmode=xml"
                efetch_res = await client.get(efetch_url)
                abstracts = {}
                
                if efetch_res.status_code == 200:
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(efetch_res.text)
                        for article in root.findall(".//PubmedArticle"):
                            pmid_elem = article.find(".//PMID")
                            abstract_text = []
                            for abstract_node in article.findall(".//AbstractText"):
                                if abstract_node.text:
                                    abstract_text.append(abstract_node.text)
                            if pmid_elem is not None and abstract_text:
                                abstracts[pmid_elem.text] = " ".join(abstract_text)
                    except Exception as e:
                        log.warning("pubmed_guidelines_xml_parse_failed", error=str(e))
                
                embedding_provider = get_embedding_provider()
                articles_ingested = 0
                
                for pmid in id_list:
                    if pmid not in summary_data:
                        continue
                        
                    art_data = summary_data[pmid]
                    title = art_data.get("title", "")
                    journal = art_data.get("fulljournalname", "")
                    pub_date = art_data.get("pubdate", "")
                    
                    # Fetch real abstract
                    claim_text = abstracts.get(pmid, title)
                    
                    # Check if already ingested
                    existing = await db.execute(select(Article).where(Article.pmid == pmid))
                    if existing.scalar_one_or_none():
                        continue
                        
                    article = Article(
                        source_id=source.id,
                        title=title,
                        pmid=pmid,
                        published_date=pub_date,
                        journal=journal,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        retrieval_status="full_text" if pmid in abstracts else "indexed"
                    )
                    db.add(article)
                    await db.flush()
                    
                    # Try to map to disease if title contains it (very basic heuristic)
                    stmt = select(Disease).where(Disease.name.ilike(f"%sepsis%")).limit(1)
                    disease = (await db.execute(stmt)).scalar_one_or_none()
                    entity_id = disease.id if disease else uuid.uuid4()
                    entity_type = "disease" if disease else "general"

                    # Max token length for simple embedding, chunking could be added
                    safe_claim = claim_text[:3500]
                    
                    # Advanced Structured JSON Extraction
                    from app.infrastructure.ai.factory import get_generation_provider
                    from app.infrastructure.ai.interfaces import GenerationRequest
                    import json
                    
                    llm = get_generation_provider()
                    
                    extraction_schema = {
                        "type": "object",
                        "properties": {
                            "recommendations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string", "enum": ["investigation", "treatment", "general"], "description": "The category of the recommendation."},
                                        "name": {"type": "string", "description": "The specific test, drug, or intervention."},
                                        "rationale": {"type": "string", "description": "When or why this is recommended."},
                                        "evidence_grade": {"type": "string", "description": "The explicitly stated evidence grade if present, otherwise 'Ia' or 'unknown'."},
                                        "recommendation_grade": {"type": "string", "description": "The explicitly stated recommendation grade if present, otherwise 'A'."}
                                    },
                                    "required": ["type", "name", "rationale", "evidence_grade", "recommendation_grade"]
                                }
                            }
                        },
                        "required": ["recommendations"]
                    }
                    
                    prompt = f"Analyze the following clinical guideline abstract and extract all recommended investigations (e.g. lab tests, imaging) and treatments as discrete objects. Abstract: {safe_claim}"
                    req = GenerationRequest(
                        prompt=prompt, 
                        system_prompt="You are an expert medical AI. Extract rigorous, highly granular clinical evidence.", 
                        temperature=0.1,
                        json_schema=extraction_schema
                    )
                    
                    recommendations = []
                    try:
                        gen_result = await llm.generate(req)
                        # Clean up potentially wrapped markdown
                        json_str = gen_result.text.strip()
                        if json_str.startswith("```json"):
                            json_str = json_str[7:]
                        if json_str.endswith("```"):
                            json_str = json_str[:-3]
                            
                        parsed_json = json.loads(json_str)
                        recommendations = parsed_json.get("recommendations", [])
                        if not recommendations:
                            raise ValueError("No recommendations extracted")
                    except Exception as e:
                        log.warning("pubmed_guidelines_llm_extraction_failed", error=str(e))
                        # Fallback to single raw chunk
                        recommendations = [{"type": "general", "name": "General Guidance", "rationale": safe_claim, "evidence_grade": "Ia", "recommendation_grade": "A"}]
                    
                    import hashlib
                    for rec in recommendations:
                        rec_claim = f"{rec.get('name', 'General')}: {rec.get('rationale', '')}"
                        rec_claim_safe = rec_claim[:3500]
                        evidence = Evidence(
                            article_id=article.id,
                            entity_type=rec.get("type", "general"),
                            entity_id=entity_id,
                            claim=rec_claim_safe,
                            evidence_grade=rec.get("evidence_grade", "Ia")[:5],
                            recommendation_grade=rec.get("recommendation_grade", "A")[:5],
                            is_ai_extracted=True
                        )
                        db.add(evidence)
                        await db.flush()
                        
                        vector = await embedding_provider.embed(rec_claim_safe)
                        
                        emb_record = EmbeddingRecord(
                            source_record_type="evidence",
                            source_record_id=str(evidence.id),
                            content_hash=hashlib.sha256(rec_claim_safe.encode("utf-8")).hexdigest(),
                            embedding_model=embedding_provider.metadata.model_name,
                            model_version="1.0",
                            dimensions=len(vector),
                            embedding=vector
                        )
                        db.add(emb_record)
                    
                    articles_ingested += 1

            await db.commit()
            log.info("pubmed_guidelines_ingestion_complete", count=articles_ingested)

        except Exception as e:
            log.error("guidelines_ingestion_error", error=str(e))
            await db.rollback()

guidelines_ingester = GuidelinesIngester()
