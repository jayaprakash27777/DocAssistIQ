"""DocAssistIQ — Knowledge Ingestion Endpoints (Phase 13).

Endpoints:
  POST   /ingestion/jobs            — Start a new ingestion job (Admin only)
  GET    /ingestion/jobs            — List ingestion jobs (Admin only)
  GET    /ingestion/jobs/{id}       — Get ingestion job details (Admin only)
  POST   /ingestion/jobs/{id}/review — Approve/reject an ingested job (Admin only)
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse
from app.authorization import require_admin
from app.dependencies import get_db
from app.exceptions import NotFoundError, ValidationError
from app.models.ingestion import IngestionJob
from app.models.provenance import Source
from app.models.user import User
from app.tasks.ingestion import run_ingestion_job

router = APIRouter(prefix="/ingestion", tags=["Knowledge Ingestion"])


class IngestionJobCreate(BaseModel):
    source_id: uuid.UUID
    source_version: str | None = None


class IngestionJobReview(BaseModel):
    review_status: Literal["approved", "rejected"]


class IngestionJobResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    source_version: str | None
    status: str
    content_hash: str | None
    raw_artifact_url: str | None
    validation_result: dict | None
    error_message: str | None
    review_status: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/jobs",
    response_model=IngestionJobResponse,
    status_code=202,
    summary="Start an ingestion job",
    responses=API_RESPONSES,
)
async def start_ingestion_job(
    payload: IngestionJobCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobResponse:
    """Start a background ingestion job for a registered source."""
    source = await db.scalar(select(Source).where(Source.id == payload.source_id))
    if not source:
        raise NotFoundError("Source not found", code="SOURCE_NOT_FOUND")
        
    if not source.is_production_suitable:
        raise ValidationError("Cannot ingest from an unverified source. Verify license terms first."
        , code="SOURCE_NOT_VERIFIED")

    # Check for already running jobs for this source
    active_job = await db.scalar(
        select(IngestionJob)
        .where(IngestionJob.source_id == payload.source_id)
        .where(IngestionJob.status.in_(["pending", "fetching", "parsing", "validating"]))
    )
    if active_job:
        raise ValidationError("An ingestion job is already running for this source."
        , code="CONCURRENT_INGESTION")

    job = IngestionJob(
        source_id=payload.source_id,
        source_version=payload.source_version,
        status="pending",
        review_status="unreviewed"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    run_ingestion_job.delay(str(job.id))

    return IngestionJobResponse.model_validate(job)


@router.get(
    "/jobs",
    response_model=PagedResponse[IngestionJobResponse],
    summary="List ingestion jobs",
    responses=API_RESPONSES,
)
async def list_ingestion_jobs(
    page: int = 1,
    page_size: int = 20,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PagedResponse[IngestionJobResponse]:
    """List knowledge ingestion jobs (Admin only)."""
    offset = (page - 1) * page_size
    from sqlalchemy import func

    count_r = await db.execute(select(func.count()).select_from(IngestionJob))
    total = count_r.scalar_one()

    result = await db.execute(
        select(IngestionJob)
        .order_by(IngestionJob.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    jobs = list(result.scalars().all())
    pages = max(1, -(-total // page_size))

    return PagedResponse(
        items=[IngestionJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobResponse,
    summary="Get ingestion job details",
    responses=API_RESPONSES,
)
async def get_ingestion_job(
    job_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobResponse:
    """Get details of a specific ingestion job."""
    job = await db.scalar(select(IngestionJob).where(IngestionJob.id == job_id))
    if not job:
        raise NotFoundError("Ingestion job not found", code="JOB_NOT_FOUND")
    return IngestionJobResponse.model_validate(job)


@router.post(
    "/jobs/{job_id}/review",
    response_model=IngestionJobResponse,
    summary="Review ingested knowledge",
    responses=API_RESPONSES,
)
async def review_ingestion_job(
    job_id: uuid.UUID,
    payload: IngestionJobReview,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobResponse:
    """Approve or reject a completed ingestion job before it affects production."""
    job = await db.scalar(select(IngestionJob).where(IngestionJob.id == job_id))
    if not job:
        raise NotFoundError("Ingestion job not found", code="JOB_NOT_FOUND")

    if job.status != "completed":
        raise ValidationError(f"Cannot review a job in state: {job.status}"
        , code="INVALID_STATE")

    if job.review_status != "unreviewed":
        raise ValidationError(f"Job is already {job.review_status}"
        , code="ALREADY_REVIEWED")

    job.review_status = payload.review_status
    
    if payload.review_status == "approved":
        # In a full implementation, this would trigger copying the normalized
        # entities to the active KnowledgeBase (Disease, Symptom, etc)
        pass

    await db.commit()
    await db.refresh(job)

    return IngestionJobResponse.model_validate(job)
