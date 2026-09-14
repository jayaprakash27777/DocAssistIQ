import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.pubmed import PubMedScannerResponse, PubMedArticle
from app.services.llm_service import llm_service
import structlog
import httpx
from urllib.parse import quote

log = structlog.get_logger(__name__)

class PubMedScannerService:
    async def scan_for_controversies(self, disease_name: str) -> PubMedScannerResponse:
        try:
            # Query PubMed E-Utilities API
            # Searching for recent controversies, adverse effects, or retractions related to the disease
            search_query = f'"{disease_name}"[Title/Abstract] AND (controversy[Title/Abstract] OR adverse[Title/Abstract] OR retract*[Title/Abstract] OR "clinical trial"[Publication Type])'
            encoded_query = quote(search_query)
            
            async with httpx.AsyncClient(timeout=4.0) as client:
                # 1. ESearch
                search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_query}&retmax=3&retmode=json&sort=date"
                search_res = await client.get(search_url)
                
                if search_res.status_code != 200:
                    return PubMedScannerResponse(disease=disease_name, controversy_found=False)
                    
                id_list = search_res.json().get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    return PubMedScannerResponse(disease=disease_name, controversy_found=False)
                
                # 2. ESummary
                ids_str = ",".join(id_list)
                summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_str}&retmode=json"
                summary_res = await client.get(summary_url)
                
                if summary_res.status_code != 200:
                    return PubMedScannerResponse(disease=disease_name, controversy_found=False)
                    
                summary_data = summary_res.json().get("result", {})
                
                articles = []
                abstracts_for_ai = []
                for pmid in id_list:
                    if pmid in summary_data:
                        art = summary_data[pmid]
                        title = art.get("title", "")
                        source = art.get("source", "")
                        pub_date = art.get("pubdate", "")
                        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        articles.append(PubMedArticle(title=title, pub_date=pub_date, source=source, url=url))
                        abstracts_for_ai.append(title)
                
                # 3. LLM Summary
                if articles:
                    system_prompt = f"You are a medical literature analyst. Summarize these recent PubMed article titles regarding '{disease_name}' into a concise 1-2 sentence warning about recent controversies or adverse effects. Titles: {'; '.join(abstracts_for_ai)}"
                    ai_summary = await llm_service.generate_text("Summarize the controversy.", system=system_prompt)
                    
                    return PubMedScannerResponse(
                        disease=disease_name,
                        controversy_found=True,
                        articles=articles,
                        ai_summary=ai_summary
                    )
                    
            return PubMedScannerResponse(disease=disease_name, controversy_found=False)
            
        except Exception as e:
            log.error("pubmed_scan_failed", error=str(e), disease=disease_name)
            return PubMedScannerResponse(disease=disease_name, controversy_found=False)

pubmed_scanner_service = PubMedScannerService()
