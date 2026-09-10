import asyncio
import sys
import os

# Add backend to sys path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.infrastructure.database import get_session_factory
from app.models.provenance import Source
from app.models.ingestion import IngestionJob
from app.tasks.ingestion import _run_ingestion_pipeline

async def run_seed():
    session_maker = get_session_factory()
    async with session_maker() as db:
        await db.begin()
        
        # OpenFDA
        source_fda = await db.scalar(select(Source).where(Source.code == "OPENFDA"))
        if not source_fda:
            source_fda = Source(
                name="OpenFDA",
                code="OPENFDA",
                organisation="U.S. FDA",
                base_url="https://api.fda.gov",
                data_type="drug_database",
                license_info="Open Data",
                is_production_suitable=True,
                status="active"
            )
            db.add(source_fda)
            await db.flush()
        
        # SymCat
        source_sym = await db.scalar(select(Source).where(Source.code == "SYMCAT"))
        if not source_sym:
            source_sym = Source(
                name="SymCat",
                code="SYMCAT",
                organisation="Columbia University",
                base_url="https://github.com/tualab/SymCat",
                data_type="clinical_guidelines",
                license_info="Open Source",
                is_production_suitable=True,
                status="active"
            )
            db.add(source_sym)
            await db.flush()
            
        # ICD10
        source_icd = await db.scalar(select(Source).where(Source.code == "ICD10"))
        if not source_icd:
            source_icd = Source(
                name="CMS ICD-10",
                code="ICD10",
                organisation="CMS",
                base_url="https://www.cms.gov",
                data_type="coding_system",
                license_info="Public Domain",
                is_production_suitable=True,
                status="active"
            )
            db.add(source_icd)
            await db.flush()
            
        await db.commit()
        await db.begin()
        
        sources = [source_fda, source_sym, source_icd]
        jobs = []
        for s in sources:
            job = IngestionJob(
                source_id=s.id,
                source_version="latest",
                status="pending",
                review_status="unreviewed"
            )
            db.add(job)
            await db.flush()
            jobs.append((s.code, job.id))
            
        await db.commit()

    print("Running Ingestion Pipeline synchronously...")
    for code, job_id in jobs:
        print(f"Running Ingestion Job for {code}...")
        try:
            await _run_ingestion_pipeline(job_id)
            print(f"Completed ingestion for {code}.")
        except Exception as e:
            print(f"Failed ingestion for {code}: {e}")
            
    print("All jobs completed!")

if __name__ == "__main__":
    asyncio.run(run_seed())
