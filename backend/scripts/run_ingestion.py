import asyncio
import structlog
import sys
import os

# Add the backend directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database import get_session_factory
from app.services.ingestion import (
    medlineplus_ingester,
    wiki_med_ingester,
    orphanet_ingester,
    clinical_trials_ingester,
)

log = structlog.get_logger(__name__)

async def run_all_ingesters():
    log.info("Starting bulk knowledge ingestion pipeline...")
    
    async with get_session_factory()() as session:
        # 1. MedlinePlus (Fastest, ~2000 topics)
        log.info("--- Starting MedlinePlus Ingestion ---")
        try:
            mplus_count = await medlineplus_ingester.ingest_xml(session)
            log.info(f"MedlinePlus Ingestion Complete. Ingested {mplus_count} topics.")
        except Exception as e:
            log.error("MedlinePlus failed", error=str(e))
            
        # 2. Orphanet (Large, ~11000 rare diseases)
        log.info("--- Starting Orphanet Ingestion ---")
        try:
            # Running on a subset to ensure it completes in reasonable time, or full if we have time
            # For demonstration, we just run the full thing. It skips already ingested ones.
            orpha_count = await orphanet_ingester.ingest_xml(session)
            log.info(f"Orphanet Ingestion Complete. Ingested {orpha_count} diseases.")
        except Exception as e:
            log.error("Orphanet failed", error=str(e))

        # 3. Clinical Trials (API based, targeted)
        log.info("--- Starting ClinicalTrials Ingestion (Sample: Diabetes) ---")
        try:
            ct_count = await clinical_trials_ingester.ingest_trials_for_condition(session, condition="Diabetes", limit=50)
            log.info(f"ClinicalTrials Ingestion Complete. Ingested {ct_count} trials.")
        except Exception as e:
            log.error("ClinicalTrials failed", error=str(e))
            
        # 4. Wikipedia Medical (API based, targeted)
        log.info("--- Starting WikiProject Medicine Ingestion (Top Articles) ---")
        try:
            wiki_titles = await wiki_med_ingester.fetch_category_members("Top-importance_medical_articles", limit=50)
            wiki_count = await wiki_med_ingester.ingest_articles(session, wiki_titles)
            log.info(f"WikiProject Medicine Ingestion Complete. Ingested {wiki_count} articles.")
        except Exception as e:
            log.error("Wikipedia failed", error=str(e))
            
    log.info("ALL INGESTION PIPELINES COMPLETED!")

if __name__ == "__main__":
    asyncio.run(run_all_ingesters())
