"""DocAssistIQ — Knowledge Ingestion Celery Tasks (Phase 13).

Pipeline: Source -> Fetch -> Parse -> Validate -> Normalize -> Hash -> Deduplicate -> Version -> Review Queue
"""

import asyncio
import hashlib
import uuid
import structlog
from celery import shared_task
from sqlalchemy import select

from app.celery_app import celery_app
from app.infrastructure.database import get_session_factory
from app.models.ingestion import IngestionJob
from app.models.provenance import Source

log = structlog.get_logger(__name__)


async def _run_ingestion_pipeline(job_id: uuid.UUID) -> None:
    """Async execution of the ingestion pipeline."""
    session_maker = get_session_factory()
    async with session_maker() as db:
        # Load job and source
        job = await db.scalar(select(IngestionJob).where(IngestionJob.id == job_id))
        if not job:
            log.error("ingestion_job_not_found", job_id=str(job_id))
            return
            
        if job.status in ("completed", "failed"):
            log.warning("ingestion_job_already_finished", job_id=str(job_id), status=job.status)
            return

        source = await db.scalar(select(Source).where(Source.id == job.source_id))
        if not source:
            job.status = "failed"
            job.error_message = "Source not found"
            await db.commit()
            return

        try:
            # 1. Fetch
            job.status = "fetching"
            await db.commit()
            # Simulated fetch
            await asyncio.sleep(1)
            raw_content = b"Simulated raw medical guidelines content."
            
            # 2. Parse
            job.status = "parsing"
            await db.commit()
            await asyncio.sleep(0.5)
            parsed_data = {"text": raw_content.decode("utf-8")}
            
            # 3. Validate
            job.status = "validating"
            await db.commit()
            await asyncio.sleep(0.5)
            job.validation_result = {"errors": [], "warnings": []}
            
            # 4. Normalize (Simulated)
            normalized_text = parsed_data["text"].lower()
            
            # 5. Hash
            content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
            job.content_hash = content_hash
            
            # 6. Deduplicate
            # Check if we already have an ingestion job with this exact hash for this source
            # that is completed and approved/unreviewed
            duplicate_job = await db.scalar(
                select(IngestionJob)
                .where(IngestionJob.source_id == source.id)
                .where(IngestionJob.content_hash == content_hash)
                .where(IngestionJob.id != job.id)
                .where(IngestionJob.status == "completed")
            )
            
            if duplicate_job:
                log.info("ingestion_duplicate_content", job_id=str(job_id), duplicate_of=str(duplicate_job.id))
                job.status = "completed"
                job.review_status = "approved"  # Already known duplicate
                job.validation_result = {"info": "Duplicate of existing content, skipped."}
                await db.commit()
                return

            # 7. Version
            # Assigning version based on source (simulated as current timestamp or source native version)
            
            # 8. Review Queue
            job.status = "completed"
            job.review_status = "unreviewed"
            await db.commit()
            
            log.info("ingestion_pipeline_success", job_id=str(job_id), source=source.code)

        except Exception as e:
            log.exception("ingestion_pipeline_failed", job_id=str(job_id), error=str(e))
            job.status = "failed"
            job.error_message = str(e)
            await db.commit()
            raise


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60, # 1 minute backoff
    time_limit=3600
)
def run_ingestion_job(self, job_id_str: str):
    """Celery task entrypoint for ingestion jobs. Handles sync -> async bridge."""
    job_id = uuid.UUID(job_id_str)
    log.info("ingestion_job_started", job_id=str(job_id))
    try:
        asyncio.run(_run_ingestion_pipeline(job_id))
    except Exception as exc:
        log.error("ingestion_job_retry", job_id=str(job_id), exc=str(exc))
        raise self.retry(exc=exc)
