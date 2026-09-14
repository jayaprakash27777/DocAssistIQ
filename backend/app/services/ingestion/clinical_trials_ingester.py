import httpx
import structlog
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Disease
from app.models.provenance import Evidence, Article, Source
from app.services.embedding_service import generate_and_store_embedding

log = structlog.get_logger(__name__)

class ClinicalTrialsIngester:
    """
    Fetches structured summaries of clinical trials from ClinicalTrials.gov API v2.
    Vectorizes the conditions and interventions as Medical Evidence.
    """
    
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self):
        self.headers = {
            "User-Agent": "DocAssistIQ/1.0 (Clinical AI Knowledge Ingestion Pipeline)"
        }

    async def fetch_recent_completed_trials(self, condition: str, limit: int = 20) -> List[dict]:
        """
        Fetches recently completed clinical trials for a specific condition.
        """
        async with httpx.AsyncClient() as client:
            params = {
                "query.cond": condition,
                "filter.overallStatus": "COMPLETED",
                "pageSize": str(limit),
                "format": "json"
            }
            try:
                response = await client.get(self.BASE_URL, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("studies", [])
            except Exception as e:
                log.error("clinical_trials_fetch_failed", error=str(e), condition=condition)
                return []
                
    async def ingest_trials_for_condition(self, db: AsyncSession, condition: str, limit: int = 20) -> int:
        """
        Ingests the fetched trials into the database as raw evidence.
        """
        studies = await self.fetch_recent_completed_trials(condition, limit)
        if not studies:
            return 0
            
        # Ensure we have a Source for ClinicalTrials.gov
        source = await db.scalar(select(Source).where(Source.name == "ClinicalTrials.gov"))
        if not source:
            source = Source(
                name="ClinicalTrials.gov",
                code="CTGOV",
                base_url="https://clinicaltrials.gov",
                credibility_tier="primary"
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)

        ingested_count = 0
        for study in studies:
            protocol = study.get("protocolSection", {})
            ident = protocol.get("identificationModule", {})
            nct_id = ident.get("nctId")
            
            if not nct_id:
                continue
                
            brief_title = ident.get("briefTitle", "")
            
            # Check if this trial article already exists
            existing_article = await db.scalar(select(Article).where(Article.title == brief_title))
            if existing_article:
                continue
                
            # Create an Article record for the Trial
            article = Article(
                source_id=source.id,
                title=brief_title,
                url=f"https://clinicaltrials.gov/study/{nct_id}",
                published_date=protocol.get("statusModule", {}).get("completionDateStruct", {}).get("date")
            )
            db.add(article)
            await db.commit()
            await db.refresh(article)
            
            # Extract Evidence (Conditions and Interventions)
            conditionsModule = protocol.get("conditionsModule", {})
            interventionsModule = protocol.get("armsInterventionsModule", {})
            descriptionModule = protocol.get("descriptionModule", {})
            
            conditions = conditionsModule.get("conditions", [])
            interventions = interventionsModule.get("interventions", [])
            summary = descriptionModule.get("briefSummary", "")
            
            if not conditions or not summary:
                continue
                
            claim = f"Clinical Trial (NCT ID: {nct_id}): {brief_title}. "
            claim += f"Conditions Studied: {', '.join(conditions)}. "
            if interventions:
                interv_names = [i.get("name", "") for i in interventions]
                claim += f"Interventions: {', '.join(interv_names)}. "
                
            evidence = Evidence(
                article_id=article.id,
                claim=claim,
                text=summary[:1000],
                evidence_grade="High",
                is_ai_extracted=False,
                status="APPROVED"
            )
            db.add(evidence)
            await db.commit()
            await db.refresh(evidence)
            
            # Generate Embeddings for the Trial Evidence
            embedding_text = f"Clinical Trial: {brief_title}\nConditions: {', '.join(conditions)}\nSummary: {summary}\n"
            try:
                await generate_and_store_embedding(
                    db=db,
                    source_record_id=str(evidence.id),
                    source_record_type="evidence",
                    content=embedding_text
                )
                ingested_count += 1
                log.info("ingested_clinical_trial", nct_id=nct_id)
            except Exception as e:
                log.error("embedding_failed_clinical_trial", error=str(e), nct_id=nct_id)
                
        return ingested_count

clinical_trials_ingester = ClinicalTrialsIngester()
