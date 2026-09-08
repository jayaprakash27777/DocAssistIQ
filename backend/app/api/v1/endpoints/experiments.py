"""DocAssistIQ — ML Experiments API Endpoints (Phase 19)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.authorization import require_admin
from app.models.user import User
from app.models.experiment import MLExperiment
from app.services import experiment_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


class ExperimentRegisterRequest(BaseModel):
    name: str
    code_commit: str
    dataset_version: str
    dataset_hash: str
    preprocessing_version: str = "1.0"
    model_name: str
    configuration: dict = {}
    random_seed: float = 42.0
    hardware: dict = {}


class ExperimentFinishRequest(BaseModel):
    status: str
    metrics: dict
    execution_duration_sec: float | None = None
    artifact_location: str | None = None


class ExperimentResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    code_commit: str
    dataset_version: str
    dataset_hash: str
    preprocessing_version: str
    model_name: str
    configuration: dict
    random_seed: float
    hardware: dict
    execution_duration_sec: float | None
    metrics: dict
    artifact_location: str | None
    
    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def register_experiment(
    payload: ExperimentRegisterRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Register a newly started ML experiment."""
    try:
        exp = await experiment_service.register_experiment(db, payload.model_dump())
        return exp
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{exp_id}", response_model=ExperimentResponse)
async def finish_experiment(
    exp_id: uuid.UUID,
    payload: ExperimentFinishRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark an ML experiment as completed or failed and record its outputs."""
    try:
        exp = await experiment_service.finish_experiment(
            db, 
            exp_id, 
            payload.status, 
            payload.metrics, 
            payload.execution_duration_sec, 
            payload.artifact_location
        )
        return exp
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all ML experiments."""
    result = await db.execute(select(MLExperiment).order_by(MLExperiment.created_at.desc()))
    return result.scalars().all()


@router.get("/{exp_id}", response_model=ExperimentResponse)
async def get_experiment(
    exp_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific ML experiment."""
    try:
        exp = await experiment_service.get_experiment(db, exp_id)
        return exp
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
