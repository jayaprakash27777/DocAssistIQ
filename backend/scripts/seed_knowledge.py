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
        print("Checking for NIH MedQuAD source...")
        source = await db.scalar(select(Source).where(Source.code == "MEDQUAD"))
        if not source:
            print("Creating NIH MedQuAD source...")
            source = Source(
                name="NIH MedQuAD",
                code="MEDQUAD",
                organisation="NIH / NLM",
                base_url="https://huggingface.co/datasets/keivalya/MedQuad-MedicalQnADataset",
                data_type="literature",
                license_info="Open Access",
                is_production_suitable=True,
                status="active"
            )
            db.add(source)
            await db.commit()
            await db.begin()
            print(f"Created Source: {source.id}")
        else:
            print("Source already exists.")

        print("Creating Ingestion Job...")
        job = IngestionJob(
            source_id=source.id,
            source_version="v1.0",
            status="pending",
            review_status="unreviewed"
        )
        db.add(job)
        await db.commit()
        await db.begin()
        job_id = job.id
        print(f"Created IngestionJob: {job_id}")

    print("Running Ingestion Pipeline Synchronously...")
    await _run_ingestion_pipeline(job_id)
    print("Ingestion Pipeline Completed.")

if __name__ == "__main__":
    asyncio.run(run_seed())
