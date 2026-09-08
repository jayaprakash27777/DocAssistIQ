"""DocAssistIQ — Dataset API Endpoints (Phase 17)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.authorization import require_admin
from app.models.user import User
from app.models.dataset import Dataset
from app.services import dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


class DatasetRegisterRequest(BaseModel):
    name: str
    source: str
    license: str
    version: str
    hash: str
    schema_def: dict
    intended_use: str
    limitations: str
    storage_path: str


class DatasetResponse(BaseModel):
    id: uuid.UUID
    name: str
    source: str
    version: str
    hash: str
    record_count: int
    is_deidentified: bool
    approval_status: str
    storage_path: str
    
    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def register_dataset(
    payload: DatasetRegisterRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Register a new dataset (pending validation)."""
    dataset_dict = payload.model_dump()
    dataset_dict["schema"] = dataset_dict.pop("schema_def")
    
    try:
        ds = await dataset_service.register_dataset(db, dataset_dict)
        return ds
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered datasets."""
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    return result.scalars().all()


@router.post("/{dataset_id}/validate")
async def validate_dataset(
    dataset_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Run the validation pipeline on the dataset."""
    try:
        result = await dataset_service.run_dataset_validation(db, dataset_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{dataset_id}/approve", response_model=DatasetResponse)
async def approve_dataset(
    dataset_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve a validated dataset for ML use."""
    try:
        ds = await dataset_service.approve_dataset(db, dataset_id)
        return ds
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
