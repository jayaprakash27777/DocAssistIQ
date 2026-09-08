"""DocAssistIQ — Evaluation API Endpoints (Phase 18)."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db
from app.authorization import require_admin
from app.models.user import User
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.services import evaluation_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


class TriggerEvaluationRequest(BaseModel):
    dataset_id: uuid.UUID
    model_version: str


class EvaluationResultResponse(BaseModel):
    id: uuid.UUID
    record_identifier: str
    task_type: str
    ground_truth: dict
    model_output: dict
    is_correct: bool | None
    score: float | None
    failure_reason: str | None
    
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    model_version: str
    status: str
    metrics: dict
    
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunDetailResponse(EvaluationRunResponse):
    results: list[EvaluationResultResponse]


@router.post("", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_evaluation(
    payload: TriggerEvaluationRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a new evaluation run for a dataset."""
    try:
        run = await evaluation_service.trigger_evaluation(
            db, payload.dataset_id, payload.model_version, admin.id
        )
        return run
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[EvaluationRunResponse])
async def list_evaluations(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all evaluation runs."""
    result = await db.execute(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()))
    return result.scalars().all()


@router.get("/{run_id}", response_model=EvaluationRunDetailResponse)
async def get_evaluation_details(
    run_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get details and record-level results for a specific evaluation run."""
    result = await db.execute(
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return run


@router.post("/{run_id}/execute")
async def execute_evaluation(
    run_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Execute the evaluation pipeline (sync for Phase 18 demo)."""
    try:
        await evaluation_service.run_evaluation_pipeline(db, run_id)
        return {"status": "completed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
