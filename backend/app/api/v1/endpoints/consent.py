"""DocAssistIQ — Consent API Endpoints (Phase 21).

Manages informed consent records.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.models.patient import ConsentRecord
from app.models.consultation import Consultation
from app.schemas.consent import ConsentRecordCreate, ConsentRecordResponse

router = APIRouter(prefix="/consent", tags=["Consent"])


@router.post("", response_model=ConsentRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_consent_record(
    payload: ConsentRecordCreate,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Record patient consent. Appends a new immutable record."""
    # Verify the doctor owns the consultation
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == payload.consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized for this consultation")
        
    consent = ConsentRecord(
        consultation_id=payload.consultation_id,
        actor_name=payload.actor_name,
        actor_relationship=payload.actor_relationship,
        purpose=payload.purpose,
        status="granted",
        recording_permitted=payload.recording_permitted,
        recorded_by_id=doctor.id,
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent


@router.post("/{consultation_id}/revoke", response_model=ConsentRecordResponse)
async def revoke_consent(
    consultation_id: uuid.UUID,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Revoke consent for a consultation. Appends a new record indicating revocation."""
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized for this consultation")
        
    # Get last consent to copy over details for the revocation record
    last_consent = await db.scalar(
        select(ConsentRecord)
        .where(ConsentRecord.consultation_id == consultation_id)
        .order_by(desc(ConsentRecord.created_at))
        .limit(1)
    )
    
    if not last_consent or last_consent.status == "revoked":
        raise HTTPException(status_code=400, detail="No active consent to revoke")
        
    revocation = ConsentRecord(
        consultation_id=consultation_id,
        actor_name=last_consent.actor_name,
        actor_relationship=last_consent.actor_relationship,
        purpose=last_consent.purpose,
        status="revoked",
        recording_permitted=False,
        recorded_by_id=doctor.id,
    )
    
    db.add(revocation)
    
    # If the consultation is actively recording, we must stop it immediately.
    # We'll pause it by transitioning to "created" state.
    if consultation.status == "recording":
        consultation.status = "created"
        
    await db.commit()
    await db.refresh(revocation)
    return revocation


@router.get("/{consultation_id}", response_model=ConsentRecordResponse)
async def get_active_consent(
    consultation_id: uuid.UUID,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent consent status for a consultation."""
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized for this consultation")
        
    last_consent = await db.scalar(
        select(ConsentRecord)
        .where(ConsentRecord.consultation_id == consultation_id)
        .order_by(desc(ConsentRecord.created_at))
        .limit(1)
    )
    
    if not last_consent:
        raise HTTPException(status_code=404, detail="No consent record found")
        
    return last_consent
