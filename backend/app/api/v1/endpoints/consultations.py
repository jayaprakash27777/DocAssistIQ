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
from app.authorization import require_permission
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.consultation import Consultation
from app.models.doctor import Doctor
from app.services import consultation_service
from app.services import doctor_service
from app.services import note_service
from app.services.audit_service import log_event
from app.services.export_service import export_service
from app.schemas.note import ClinicalNoteResponse, ClinicalNoteUpdate

router = APIRouter(prefix="/consultations", tags=["Consultations"])

async def get_current_doctor_profile(
    user: User = Depends(get_current_user),
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

class PaginatedConsultations(BaseModel):
    items: list[ConsultationResponse]
    total: int
    page: int
    page_size: int
    pages: int


@router.post("", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    payload: ConsultationCreateRequest,
    user: User = Depends(require_permission("consultation", "create")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Create a new consultation in the CREATED state."""
    consultation = await consultation_service.create_consultation(
        db, doctor.id, user.id, payload.patient_session_id, payload.input_text
    )
    
    await log_event(
        db,
        action="consultation.created",
        entity_type="consultation",
        entity_id=consultation.id,
        actor_id=user.id,
        severity="info",
    )
    
    return consultation


@router.get("", response_model=PaginatedConsultations)
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
    user: User = Depends(require_permission("consultation", "read")),
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
        
    await log_event(
        db,
        action="consultation.accessed",
        entity_type="consultation",
        entity_id=consultation.id,
        actor_id=user.id,
        severity="info",
    )
    
    return consultation


@router.patch("/{consultation_id}/status", response_model=ConsultationResponse)
async def transition_consultation_status(
    consultation_id: uuid.UUID,
    payload: ConsultationTransitionRequest,
    user: User = Depends(require_permission("consultation", "update")),
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
    user: User = Depends(require_permission("consultation", "read")),
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
    user: User = Depends(require_permission("consultation", "read")),
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
    user: User = Depends(require_permission("consultation", "update")),
    doctor: Doctor = Depends(get_current_doctor_profile),
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
        finding.confirmed_by_id = user.id
    elif payload.action == "reject":
        finding.is_clinician_confirmed = False
        finding.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Action must be 'confirm' or 'reject'")
    
    await db.commit()
    await db.refresh(finding)
    return finding


@router.post("/{consultation_id}/events", response_model=ConsultationEventResponse)
async def create_consultation_event(
    consultation_id: uuid.UUID,
    payload: ConsultationEventCreate,
    user: User = Depends(require_permission("consultation", "update")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Record an arbitrary timeline event for the consultation (e.g. system notification)."""
    return await timeline_service.create_consultation_event(db, consultation_id, user.id, payload)


@router.get("/{consultation_id}/disease-intelligence")
async def get_disease_intelligence(
    consultation_id: uuid.UUID,
    disease: str = Query(..., description="Name of the disease to profile"),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Generate a geographic/travel-aware disease intelligence profile."""
    # Ensure consultation exists and doctor has access
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    from app.services.disease_intelligence_service import generate_disease_intelligence
    return await generate_disease_intelligence(db, disease)


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
    from app.services.diagnosis_provider import OllamaDiagnosisProvider
    
    from app.services.safety_engine import safety_engine
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id)
    
    provider = OllamaDiagnosisProvider()
    response = await provider.generate_differential(db, rep)
    
    # Phase 41: Evaluate safety for each differential candidate
    for item in response.top_candidates:
        safety_decision = await safety_engine.evaluate_differential_item(db, item, rep)
        item.safety_decision = safety_decision
        
    return response

from app.schemas.investigation import InvestigationResponse

@router.get("/{consultation_id}/investigations", response_model=InvestigationResponse)
async def get_investigations_for_disease(
    consultation_id: uuid.UUID,
    disease: str,
    competing: list[str] = Query(default=[]),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Phase 44: Returns reference intelligence for investigations."""
    from app.services.investigation_service import investigation_provider
    from app.services.representation_service import build_clinical_representation
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id)
    return await investigation_provider.get_investigations(db, disease, rep, competing)

from app.schemas.medication import MedicationResponse
from app.schemas.early_warning import EarlyWarningResponse
from app.schemas.epidemiology import EpiRadarResponse
from app.schemas.pubmed import PubMedScannerResponse

@router.get("/{consultation_id}/pubmed-scanner", response_model=PubMedScannerResponse)
async def get_pubmed_controversies(
    consultation_id: uuid.UUID,
    disease: str,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """PubMed Bleeding-Edge Controversy Scanner"""
    from app.services.pubmed_scanner_service import pubmed_scanner_service
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    return await pubmed_scanner_service.scan_for_controversies(disease)

@router.get("/{consultation_id}/epi-radar", response_model=EpiRadarResponse)
async def get_epi_radar_surveillance(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Real-Time Epidemiological Radar"""
    from app.services.epidemiology_service import epi_radar_service
    from app.services.representation_service import build_clinical_representation
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id)
    return await epi_radar_service.evaluate_syndromic_surveillance(db, consultation_id, rep)

@router.get("/{consultation_id}/early-warning", response_model=EarlyWarningResponse)
async def get_early_warning_evaluation(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Predictive Deterioration & Sepsis EWS"""
    from app.services.early_warning_service import early_warning_service
    from app.services.representation_service import build_clinical_representation
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id)
    return await early_warning_service.evaluate_deterioration_risk(db, consultation_id, rep)

@router.get("/{consultation_id}/medications", response_model=MedicationResponse)
async def get_medications_for_disease(
    consultation_id: uuid.UUID,
    disease: str,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Phase 45: Returns reference intelligence for medications."""
    from app.services.medication_service import medication_provider
    from app.services.representation_service import build_clinical_representation
    from app.services.safety_engine import safety_engine
    from app.models.patient_profile import PatientProfile
    from app.models.patient import PatientSession
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    response = await medication_provider.get_medications(db, disease)
    rep = await build_clinical_representation(db, consultation_id)
    
    patient_profile = None
    if consultation.patient_session_id:
        stmt = (
            select(PatientProfile)
            .join(PatientSession, PatientProfile.id == PatientSession.patient_profile_id)
            .where(PatientSession.id == consultation.patient_session_id)
        )
        patient_profile = await db.scalar(stmt)
    
    # Phase 46: Evaluate safety for each medication candidate
    for item in response.suggestions:
        safety_decision = await safety_engine.evaluate_medication(item, rep, patient_profile)
        item.safety_decision = safety_decision
        
    return response

@router.get("/{consultation_id}/export")
async def export_consultation(
    consultation_id: uuid.UUID,
    format: str = "pdf",
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a finalized consultation note.
    Formats supported: 'pdf' (markdown representation), 'fhir'
    """
    consultation = await consultation_service.get_consultation(db, consultation_id, doctor.id)
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    if consultation.status not in ["finalized", "amended"]:
        raise HTTPException(status_code=400, detail="Only finalized consultations can be exported")

    # Fetch the note data
    note_data = None
    try:
        note_data_raw = await note_service.get_clinical_note(db, consultation_id)
        if note_data_raw:
            note_data = ClinicalNoteResponse.model_validate(note_data_raw)
    except Exception:
        pass # Note might not exist if empty, though it should

    if format.lower() == "fhir":
        return export_service.generate_fhir_document_reference(consultation, note_data)
    elif format.lower() == "pdf":
        from fastapi import Response
        pdf_bytes = export_service.generate_pdf(consultation, note_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="consultation_{consultation_id}.pdf"'}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

@router.get("/{consultation_id}/audit")
async def get_consultation_audit(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the audit trail and consent records for a consultation.
    """
    consultation = await consultation_service.get_consultation(db, consultation_id, doctor.id)
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    from app.models.patient import ConsentRecord
    from app.models.consultation import ConsultationAudit
    from app.schemas.consent import ConsentRecordResponse
    from app.schemas.consultation import ConsultationAuditResponse
    
    # Get audit events
    audit_stmt = select(ConsultationAudit).where(ConsultationAudit.consultation_id == consultation_id).order_by(ConsultationAudit.created_at.desc())
    audit_events = (await db.execute(audit_stmt)).scalars().all()
    
    # Get consent records
    consent_stmt = select(ConsentRecord).where(ConsentRecord.consultation_id == consultation_id).order_by(ConsentRecord.created_at.desc())
    consent_records = (await db.execute(consent_stmt)).scalars().all()
    
    return {
        "audits": [ConsultationAuditResponse.model_validate(a) for a in audit_events],
        "consents": [ConsentRecordResponse.model_validate(c) for c in consent_records]
    }

@router.get("/{consultation_id}/similar-cases")
async def get_similar_cases(
    consultation_id: uuid.UUID,
    limit: int = 5,
    user: User = Depends(require_permission("consultation", "read")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Phase 50: Retrieve similar historical cases using pgvector similarity search."""
    from app.services.case_retrieval import find_similar_cases
    
    # Ensure doctor owns the consultation
    await consultation_service.get_consultation(db, consultation_id, doctor.id)
    
    similar_cases = await find_similar_cases(db, consultation_id, limit)
    return {"cases": similar_cases}

from app.schemas.polypharmacy import PolypharmacyRequest, PolypharmacyResponse

@router.post("/{consultation_id}/polypharmacy-simulate", response_model=PolypharmacyResponse)
async def simulate_polypharmacy(
    consultation_id: uuid.UUID,
    payload: PolypharmacyRequest,
    user: User = Depends(require_permission("consultation", "read")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Simulate drug interactions using LLM."""
    from app.services.polypharmacy_service import polypharmacy_simulator
    from app.services.representation_service import build_clinical_representation
    from app.models.patient_profile import PatientProfile
    from app.models.patient import PatientSession
    
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id)
    
    current_meds = [m.value.lower() for m in rep.medications]
    
    if consultation.patient_session_id:
        stmt = (
            select(PatientProfile)
            .join(PatientSession, PatientProfile.id == PatientSession.patient_profile_id)
            .where(PatientSession.id == consultation.patient_session_id)
        )
        patient_profile = await db.scalar(stmt)
        if patient_profile and patient_profile.baseline_conditions:
            structured_meds = patient_profile.baseline_conditions.get("current_medications", [])
            for sm in structured_meds:
                if sm.lower() not in current_meds:
                    current_meds.append(sm.lower())
                    
    return await polypharmacy_simulator.simulate(
        proposed_meds=payload.proposed_medications,
        current_meds=current_meds
    )
