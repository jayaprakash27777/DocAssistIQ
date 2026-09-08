"""DocAssistIQ — Manual Intake API Endpoints (Phase 22)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.models.clinical import ManualIntake
from app.models.consultation import Consultation
from app.schemas.intake import ManualIntakeUpdate, ManualIntakeResponse

router = APIRouter(prefix="/consultations", tags=["Manual Intake"])


@router.get("/{consultation_id}/intake", response_model=ManualIntakeResponse)
async def get_intake(
    consultation_id: uuid.UUID,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the manual intake draft for a consultation."""
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    intake = await db.scalar(
        select(ManualIntake).where(ManualIntake.consultation_id == consultation_id)
    )
    
    if not intake:
        # Create a blank draft automatically if requested
        intake = ManualIntake(
            consultation_id=consultation_id,
            doctor_id=doctor.id,
            status="draft",
        )
        db.add(intake)
        await db.commit()
        await db.refresh(intake)
        
    return intake


@router.patch("/{consultation_id}/intake", response_model=ManualIntakeResponse)
async def update_intake(
    consultation_id: uuid.UUID,
    payload: ManualIntakeUpdate,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Autosave/update the manual intake draft."""
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    intake = await db.scalar(
        select(ManualIntake).where(ManualIntake.consultation_id == consultation_id)
    )
    
    if not intake:
        intake = ManualIntake(
            consultation_id=consultation_id,
            doctor_id=doctor.id,
            status="draft",
        )
        db.add(intake)
        
    if intake.status == "final":
        raise HTTPException(status_code=400, detail="Cannot edit a finalized intake")

    # Update fields
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(intake, field, value)

    await db.commit()
    await db.refresh(intake)
    return intake


@router.post("/{consultation_id}/intake/finalize", response_model=ManualIntakeResponse)
async def finalize_intake(
    consultation_id: uuid.UUID,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Mark the manual intake as final."""
    intake = await db.scalar(
        select(ManualIntake).where(ManualIntake.consultation_id == consultation_id)
    )
    if not intake or intake.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Intake not found or unauthorized")
        
    intake.status = "final"
    await db.commit()
    await db.refresh(intake)
    return intake
