import uuid
import structlog
import httpx
from typing import List, Optional
from xml.etree import ElementTree as ET

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.provenance import Source, Article, Evidence
from app.models.embedding import EmbeddingRecord
from app.infrastructure.ai.factory import get_embedding_provider
from app.config import get_settings

log = structlog.get_logger(__name__)

class PMCIngester:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def ingest_corpus(self, db: AsyncSession, max_articles: int = 100):
        """
        Fetches recent Open Access PMC articles, generates embeddings, and stores them
        for RAG retrieval.
        """
        try:
            # 1. Ensure the PMC Source exists
            stmt = select(Source).where(Source.code == "pmc_open_access")
            result = await db.execute(stmt)
            source = result.scalar_one_or_none()

            if not source:
                source = Source(
                    code="pmc_open_access",
                    organisation="NIH / NLM",
                    name="PubMed Central Open Access",
                    base_url=self.base_url,
                    access_mechanism="api",
                    data_type="literature",
                    is_production_suitable=True,
                    status="active"
                )
                db.add(source)
                await db.flush()

            # 2. Search for recent articles (e.g. "Sepsis" or general medical topics)
            search_query = '("open access"[filter]) AND (clinical trial[ptyp] OR review[ptyp])'
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                search_url = f"{self.base_url}/esearch.fcgi?db=pmc&term={search_query}&retmax={max_articles}&retmode=json"
                search_res = await client.get(search_url)
                
                if search_res.status_code != 200:
                    log.error("pmc_esearch_failed", status=search_res.status_code)
                    return
                    
                id_list = search_res.json().get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    log.info("pmc_no_articles_found")
                    return
                
                # 3. Fetch Summaries / Abstracts
                ids_str = ",".join(id_list)
                summary_url = f"{self.base_url}/esummary.fcgi?db=pmc&id={ids_str}&retmode=json"
                summary_res = await client.get(summary_url)
                
                if summary_res.status_code != 200:
                    log.error("pmc_esummary_failed")
                    return
                    
                summary_data = summary_res.json().get("result", {})
                
                embedding_provider = get_embedding_provider()
                
                articles_ingested = 0
                for pmcid in id_list:
                    if pmcid not in summary_data:
                        continue
                        
                    art_data = summary_data[pmcid]
                    title = art_data.get("title", "")
                    journal = art_data.get("fulljournalname", "")
                    pub_date = art_data.get("pubdate", "")
                    doi = art_data.get("doi", "")
                    
                    # Check if already ingested
                    existing = await db.execute(select(Article).where(Article.pmid == pmcid))
                    if existing.scalar_one_or_none():
                        continue
                        
                    # Create Article
                    article = Article(
                        source_id=source.id,
                        title=title,
                        doi=doi,
                        pmid=pmcid, # Using PMCID as PMID for simplicity here
                        published_date=pub_date,
                        journal=journal,
                        url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
                        retrieval_status="indexed"
                    )
                    db.add(article)
                    await db.flush()
                    
                    claim_text = title
                    entity_type = "general"
                    entity_id = uuid.uuid4()
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
                    
                    prompt = f"Analyze the following abstract and extract all recommended investigations (e.g. lab tests, imaging) and treatments as discrete objects. Abstract: {safe_claim}"
                    req = GenerationRequest(
                        prompt=prompt, 
                        system_prompt="You are an expert medical AI. Extract rigorous, highly granular clinical evidence.", 
                        temperature=0.1,
                        json_schema=extraction_schema
                    )
                    
                    recommendations = []
                    try:
                        gen_result = await llm.generate(req)
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
                        log.warning("pmc_rag_llm_extraction_failed", error=str(e))
                        recommendations = [{"type": "general", "name": "General Evidence", "rationale": safe_claim, "evidence_grade": "Ia", "recommendation_grade": "A"}]
                    
                    import hashlib
                    for rec in recommendations:
                        rec_claim = f"{rec.get('name', 'General')}: {rec.get('rationale', '')}"
                        rec_claim_safe = rec_claim[:3500]
                        evidence = Evidence(
                            article_id=article.id,
                            entity_type=rec.get("type", "general"),
                            entity_id=entity_id,
                            claim=rec_claim_safe,
                            evidence_grade=rec.get("evidence_grade", "Ia")[:5], # Or IIa depending on journal
                            recommendation_grade=rec.get("recommendation_grade", "A")[:5],
                            is_ai_extracted=True
                        )
                        db.add(evidence)
                        await db.flush()
                        
                        # Generate Vector Embedding
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
                log.info("pmc_ingestion_complete", articles_ingested=articles_ingested)

        except Exception as e:
            log.error("pmc_ingestion_error", error=str(e))
            await db.rollback()

pmc_ingester = PMCIngester()
