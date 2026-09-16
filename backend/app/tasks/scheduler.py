"""DocAssistIQ — Continuous Knowledge Update Scheduler (Phase 48).

Scheduled Celery task that periodically scans verified sources
and triggers the ingestion pipeline for any sources needing updates.
"""

import asyncio
import httpx
import structlog
from celery import shared_task
from sqlalchemy import select

from app.celery_app import celery_app
from app.infrastructure.database import get_session_factory
from app.models.provenance import Source
from app.models.ingestion import IngestionJob
from app.tasks.ingestion import run_ingestion_job

log = structlog.get_logger(__name__)

async def _schedule_continuous_updates() -> None:
    """Async implementation to query sources and queue jobs."""
    db = get_session_factory()()
    try:
        await db.begin()
        
        # Select sources that are active and production suitable
        stmt = select(Source).where(
            Source.is_production_suitable == True,
            Source.status == "registered"
        )
        result = await db.execute(stmt)
        sources = result.scalars().all()
        
        if not sources:
            log.info("continuous_update_scheduler_no_sources")
            return
            
        jobs_queued = 0
        for source in sources:
            # Check if there's already a pending or fetching job for this source
            pending_stmt = select(IngestionJob).where(
                IngestionJob.source_id == source.id,
                IngestionJob.status.in_(["pending", "fetching", "parsing", "validating"])
            )
            pending_result = await db.execute(pending_stmt)
            existing_job = pending_result.scalar_one_or_none()
            
            if existing_job:
                log.debug("continuous_update_scheduler_skip_active", source_id=str(source.id))
                continue
                
            # Create new job
            new_job = IngestionJob(
                source_id=source.id,
                status="pending",
                review_status="unreviewed"
            )
            db.add(new_job)
            await db.flush()
            
            # Queue to worker
            run_ingestion_job.delay(str(new_job.id))
            jobs_queued += 1
            
        await db.commit()
        log.info("continuous_update_scheduler_completed", queued=jobs_queued)
        
    except Exception as e:
        log.exception("continuous_update_scheduler_failed", error=str(e))
        await db.rollback()
    finally:
        await db.close()


@celery_app.task(
    bind=True,
    time_limit=300
)
def task_schedule_continuous_updates(self):
    """Celery beat task to periodically schedule knowledge updates."""
    log.info("continuous_update_scheduler_started")
    asyncio.run(_schedule_continuous_updates())

async def _sync_fda_warnings() -> None:
    """Hits the real api.fda.gov to sync active drug warnings into the ingestion queue."""
    db = get_session_factory()()
    try:
        await db.begin()
        
        # Select the FDA source
        stmt = select(Source).where(Source.name == "OpenFDA Medical Devices & Drugs").limit(1)
        result = await db.execute(stmt)
        fda_source = result.scalar_one_or_none()
        
        if not fda_source:
            log.info("sync_fda_warnings_skipped", reason="FDA Source not registered in DB")
            await db.rollback()
            return
            
        # REAL LIVE DATA: Hit the actual FDA API for new drug labels
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.fda.gov/drug/label.json?search=effective_time:[20230101+TO+20240101]&limit=5")
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    # Queue an ingestion job for this source
                    new_job = IngestionJob(
                        source_id=fda_source.id,
                        status="pending",
                        review_status="unreviewed"
                    )
                    db.add(new_job)
                    await db.commit()
                    log.info("sync_fda_warnings_success", job_id=str(new_job.id), pulled_records=len(results))
                else:
                    await db.rollback()
            else:
                await db.rollback()
                    
    except Exception as e:
        log.exception("sync_fda_warnings_failed", error=str(e))
        await db.rollback()
    finally:
        await db.close()

@celery_app.task(
    bind=True,
    time_limit=120
)
def task_sync_fda_warnings(self):
    """Celery beat task to pull live data from FDA."""
    log.info("sync_fda_warnings_task_started")
    asyncio.run(_sync_fda_warnings())
