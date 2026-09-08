"""DocAssistIQ — ML Experiment Service (Phase 19).

Handles experiment registration, updating metrics, and saving artifacts.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.models.experiment import MLExperiment


async def register_experiment(db: AsyncSession, payload: dict) -> MLExperiment:
    """Registers a new ML experiment (started state)."""
    
    exp = MLExperiment(
        name=payload["name"],
        status="running",
        code_commit=payload["code_commit"],
        dataset_version=payload["dataset_version"],
        dataset_hash=payload["dataset_hash"],
        preprocessing_version=payload.get("preprocessing_version", "1.0"),
        model_name=payload["model_name"],
        configuration=payload.get("configuration", {}),
        random_seed=payload.get("random_seed", 42),
        hardware=payload.get("hardware", {}),
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return exp


async def get_experiment(db: AsyncSession, exp_id: uuid.UUID) -> MLExperiment:
    exp = await db.get(MLExperiment, exp_id)
    if not exp:
        raise NotFoundError("Experiment not found", code="EXPERIMENT_NOT_FOUND")
    return exp


async def finish_experiment(
    db: AsyncSession, 
    exp_id: uuid.UUID, 
    status: str, 
    metrics: dict, 
    duration_sec: float | None = None,
    artifact_location: str | None = None
) -> MLExperiment:
    """Mark an experiment as completed/failed and record its outputs."""
    exp = await get_experiment(db, exp_id)
    
    if status not in ["completed", "failed", "aborted"]:
        raise ValidationError(f"Cannot finish experiment with status {status}", code="INVALID_STATUS")
        
    exp.status = status
    exp.metrics = metrics
    
    if duration_sec is not None:
        exp.execution_duration_sec = duration_sec
        
    if artifact_location is not None:
        exp.artifact_location = artifact_location
        
    await db.commit()
    await db.refresh(exp)
    return exp
