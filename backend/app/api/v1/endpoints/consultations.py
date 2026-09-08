"""DocAssistIQ — Consultation API Endpoints (Phase 20).

Provides a validated state machine for the consultation lifecycle.
"""

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.models.consultation import Consultation
from app.models.doctor import Doctor
from app.services import consultation_service
from app.services import doctor_service
from app.services import note_service
from app.schemas.note import ClinicalNoteResponse, ClinicalNoteUpdate

router = APIRouter(prefix="/consultations", tags=["Consultations"])

async def get_current_doctor_profile(
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
) -> Doctor:
    """Fetch the current user's doctor profile."""
    doctor = await doctor_service.get_doctor_by_user(db, user.id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor profile not found. Please complete profile setup."
        )
    return doctor


class ConsultationCreateRequest(BaseModel):
    patient_session_id: uuid.UUID | None = None
    input_text: str | None = None


class ConsultationTransitionRequest(BaseModel):
    new_status: str
    input_text: str | None = None


class ClinicalFindingResponse(BaseModel):
    id: uuid.UUID
    finding_type: str
    finding_text: str
    concept: str | None
    value: str | None
    certainty: str | None
    negated: bool
    temporality: str | None
    source_context: str | None
    is_ai_suggested: bool
    is_clinician_confirmed: bool
    status: str
    confidence_score: float | None

    model_config = ConfigDict(from_attributes=True)

class ConsultationResponse(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_session_id: uuid.UUID | None
    status: str
    input_text: str
    created_at: Any
    updated_at: Any
    findings: list[ClinicalFindingResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    payload: ConsultationCreateRequest,
    user: User = Depends(require_doctor),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Create a new consultation in the CREATED state."""
    consultation = await consultation_service.create_consultation(
        db, doctor.id, user.id, payload.patient_session_id, payload.input_text
    )
    return consultation


@router.get("", response_model=dict)
async def list_consultations(
    page: int = 1,
    page_size: int = 20,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """List consultations for the logged-in doctor (paginated)."""
    limit = page_size
    offset = (page - 1) * page_size
    consultations, total = await consultation_service.list_consultations(
        db, doctor.id, limit, offset
    )
    import math
    pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    return {
        "items": consultations,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a specific consultation with findings."""
    consultation = await db.scalar(
        select(Consultation)
        .options(selectinload(Consultation.findings))
        .where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    return consultation


@router.patch("/{consultation_id}/status", response_model=ConsultationResponse)
async def transition_consultation_status(
    consultation_id: uuid.UUID,
    payload: ConsultationTransitionRequest,
    user: User = Depends(require_doctor),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Transition a consultation to a new status.
    Idempotent: If it's already in the target status, updates the input_text and returns 200.
    """
    consultation = await consultation_service.update_consultation_state(
        db=db,
        consultation_id=consultation_id,
        doctor_id=doctor.id,
        actor_id=user.id,
        new_state=payload.new_status,
        input_text=payload.input_text
    )
    return consultation

@router.get("/{consultation_id}/note", response_model=ClinicalNoteResponse)
async def get_consultation_note(
    consultation_id: uuid.UUID,
    user: User = Depends(require_doctor),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the clinical note for a specific consultation."""
    # Ensure doctor owns the consultation
    await consultation_service.get_consultation(db, consultation_id, doctor.id)
    return await note_service.get_clinical_note(db, consultation_id)

@router.patch("/{consultation_id}/note", response_model=ClinicalNoteResponse)
async def update_consultation_note(
    consultation_id: uuid.UUID,
    payload: ClinicalNoteUpdate,
    user: User = Depends(require_doctor),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update the clinical note enforcing optimistic concurrency.
    
    Accepts either:
    - {"body": {"assessment": "..."}, "version": 1}  — full replacement
    - {"sections": {"assessment": "..."}, "version": 1}  — partial merge
    """
    # Ensure doctor owns the consultation
    await consultation_service.get_consultation(db, consultation_id, doctor.id)
    # Get current note to compute merged body
    current_note = await note_service.get_clinical_note(db, consultation_id)
    merged_body = payload.get_merged_body(current_note.body or {})
    return await note_service.update_clinical_note(
        db=db,
        consultation_id=consultation_id,
        actor_id=user.id,
        body=merged_body,
        version=payload.version
    )

class FindingReviewRequest(BaseModel):
    action: str  # 'confirm' or 'reject'

@router.patch("/{consultation_id}/findings/{finding_id}", response_model=ClinicalFindingResponse)
async def review_clinical_finding(
    consultation_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: FindingReviewRequest,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Confirm or reject an AI-suggested clinical finding."""
    from app.models.clinical import ClinicalFinding
    
    finding = await db.scalar(
        select(ClinicalFinding).where(
            ClinicalFinding.id == finding_id,
            ClinicalFinding.consultation_id == consultation_id
        )
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    # Security: Ensure doctor owns the consultation
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if payload.action == "confirm":
        finding.is_clinician_confirmed = True
        finding.status = "confirmed"
        finding.confirmed_by_id = doctor.id
    elif payload.action == "reject":
        finding.is_clinician_confirmed = False
        finding.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Action must be 'confirm' or 'reject'")
    
    await db.commit()
    await db.refresh(finding)
    return finding


@router.get("/{consultation_id}/representation")
async def get_clinical_representation(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    from app.services.representation_service import build_clinical_representation
    from app.services.safety_engine import safety_engine
    
    # Check if consultation exists and is owned by doctor
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id)
    
    # Phase 42: Evaluate clinical representation against red-flag rules
    safety_decision = await safety_engine.evaluate_clinical_representation(rep)
    rep.safety_decision = safety_decision
    
    return rep

@router.get("/{consultation_id}/differential")
async def get_differential_diagnosis(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    from app.services.representation_service import build_clinical_representation
    from app.services.diagnosis_provider import BaselineDiagnosisProvider
    
    from app.services.safety_engine import safety_engine
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id)
    
    provider = BaselineDiagnosisProvider()
    response = await provider.generate_differential(rep)
    
    # Phase 41: Evaluate safety for each differential candidate
    for item in response.top_candidates:
        safety_decision = await safety_engine.evaluate_differential_item(db, item, rep)
        item.safety_decision = safety_decision
        
    return response

@router.get("/{consultation_id}/investigations")
async def get_investigations_for_disease(
    consultation_id: uuid.UUID,
    disease: str,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Phase 44: Returns reference intelligence for investigations."""
    from app.services.investigation_service import investigation_provider
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    return investigation_provider.get_investigations(disease)
