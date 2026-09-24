"""DocAssistIQ — Consultation API Endpoints (Phase 20).

Provides a validated state machine for the consultation lifecycle.
"""

import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.platform import API_RESPONSES
from app.authorization import require_permission
from app.dependencies import get_current_user, get_db, _bearer_scheme, get_settings_dep
from app.config import Settings
from app.models.user import User
from app.models.consultation import Consultation
from app.models.doctor import Doctor
from app.services import consultation_service
from app.services import doctor_service
from app.services import note_service
from app.services.note_generator import note_generator_service
from app.services.audit_service import log_event
from app.services.export_service import export_service
from app.schemas.note import ClinicalNoteResponse, ClinicalNoteUpdate
from app.schemas.consultation import ConsultationEventCreate, ConsultationEventResponse

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


async def get_optional_doctor_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> Optional[Doctor]:
    """Fetch the doctor profile if a valid Bearer token is supplied, else None."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        from app.services import auth_service
        user = await auth_service.get_current_user(
            token=credentials.credentials,
            session=db,
            settings=settings,
        )
        if user:
            return await doctor_service.get_doctor_by_user(db, user.id)
    except Exception:
        return None
    return None


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


@router.get("", response_model=Union[PaginatedConsultations, list[ConsultationResponse]])
async def list_consultations(
    page: Optional[int] = Query(None),
    page_size: Optional[int] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
    query: Optional[str] = Query(None),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    List consultations for the logged-in doctor.
    Dual client support:
    - If `page` is provided (frontend UI pagination), returns PaginatedConsultations.
    - If `page` is omitted (backend tests, search, or offset/limit queries), returns list[ConsultationResponse].
    """
    if page is not None:
        ps = page_size or 20
        calc_offset = (page - 1) * ps
        consultations, total = await consultation_service.list_consultations(
            db, doctor.id, limit=ps, offset=calc_offset
        )
        import math
        pages = max(1, math.ceil(total / ps)) if total > 0 else 1
        return {
            "items": consultations,
            "total": total,
            "page": page,
            "page_size": ps,
            "pages": pages,
        }
    else:
        eff_limit = limit if limit is not None else 100
        eff_offset = offset if offset is not None else 0
        consultations, total = await consultation_service.list_consultations(
            db, doctor.id, limit=eff_limit, offset=eff_offset
        )
        return consultations


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

@router.post("/{consultation_id}/notes/generate", response_model=ClinicalNoteResponse)
@router.post("/{consultation_id}/note/generate", response_model=ClinicalNoteResponse)
async def generate_consultation_note(
    consultation_id: uuid.UUID,
    payload: Optional[Dict[str, Any]] = None,
    user: User = Depends(require_permission("consultation", "read")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Generate or update clinical note from findings, input text, and transcript."""
    # Ensure doctor owns the consultation
    consultation = await consultation_service.get_consultation(db, consultation_id, doctor.id)
    payload_data = payload or {}
    transcript_text = payload_data.get("transcript_text", "")
    transcript_segments = payload_data.get("transcript_segments", None)

    if transcript_text and not consultation.input_text:
        consultation.input_text = transcript_text
        await db.commit()
        await db.refresh(consultation)

    note = await note_generator_service.draft_note_from_findings(
        db, consultation_id, user.id, transcript_segments=transcript_segments
    )
    return note

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
    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if consultation and consultation.doctor_id != doctor.id:
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
    symptoms: str = Query(default="", description="Comma-separated symptoms (optional, supplements DB data)"),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Real-time AI differential diagnosis.

    Priority:
      1. Use clinical DB data (findings, manual intake, transcript)
      2. If DB has no symptoms → use `symptoms` query param
      3. If both empty → return INSUFFICIENT_INFO with guidance
      4. Always runs deterministic ClinicalReasoningEngine (instant)
      5. Adds real-time medical intelligence from live APIs
    """
    import asyncio
    from app.services.representation_service import build_clinical_representation
    from app.services.diagnosis_provider import OllamaDiagnosisProvider, BaselineDiagnosisProvider
    from app.services.safety_engine import safety_engine
    from app.schemas.representation import RepresentationItem, Provenance
    from datetime import datetime, timezone

    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Build representation from DB
    rep = await build_clinical_representation(db, consultation_id)

    # If clinical notes or symptoms query provided, parse with high-speed clinical note parser
    notes_to_parse = symptoms.strip() if (symptoms and symptoms.strip()) else (consultation.input_text.strip() if (consultation and consultation.input_text) else "")
    if notes_to_parse:
        from app.services.clinical_note_parser import clinical_note_parser
        parsed = clinical_note_parser.parse(notes_to_parse)
        prov = Provenance(
            source_type="clinical_note_query",
            source_id=str(consultation_id),
            timestamp=datetime.now(timezone.utc),
            author_id=str(doctor.id),
        )

        if parsed.get("positive_findings"):
            for f in parsed["positive_findings"]:
                if not any(item.value.lower() == f.lower() for item in rep.symptoms):
                    rep.symptoms.append(
                        RepresentationItem(value=f, concept=None, status=None, provenances=[prov])
                    )
        elif not rep.symptoms:
            user_symptoms = [s.strip() for s in notes_to_parse.split(",") if s.strip()]
            for sym in user_symptoms:
                if not any(item.value.lower() == sym.lower() for item in rep.symptoms):
                    rep.symptoms.append(
                        RepresentationItem(value=sym, concept=None, status=None, provenances=[prov])
                    )

        if parsed.get("negated_findings"):
            for nf in parsed["negated_findings"]:
                if not any(item.value.lower() == nf.lower() for item in rep.negations):
                    rep.negations.append(
                        RepresentationItem(value=nf, concept=None, status="absent", provenances=[prov])
                    )

        if parsed.get("travel_history"):
            for th in parsed["travel_history"]:
                if not any(item.value.lower() == th.lower() for item in rep.travel_history):
                    rep.travel_history.append(
                        RepresentationItem(value=th, concept=None, status=None, provenances=[prov])
                    )

        if not rep.duration:
            rep.duration.append(
                RepresentationItem(value="acute (days)", concept=None, status=None, provenances=[prov])
            )
        if not rep.severity:
            rep.severity.append(
                RepresentationItem(value="moderate", concept=None, status=None, provenances=[prov])
            )

    # Run full precision AI diagnosis (instant deterministic + LLM narrative & open-domain)
    provider = OllamaDiagnosisProvider()
    try:
        response = await asyncio.wait_for(
            provider.generate_differential(db, rep),
            timeout=10.0,  # real-time budget: deterministic instant + fast LLM narrative
        )
    except asyncio.TimeoutError:
        # Absolute fallback: very fast deterministic only
        from app.services.diagnosis_provider import _extract_fields
        from app.services.clinical_reasoning_engine import clinical_reasoning_engine
        from app.schemas.diagnosis import DifferentialDiagnosisItem

        if rep.symptoms:
            fields = _extract_fields(rep)
            scored = clinical_reasoning_engine.score_all_diseases(
                patient_symptoms=fields["patient_symptoms"],
                negated_symptoms=fields["negated_symptoms"],
                countries_visited=fields["countries_visited"],
                days_since_return=fields["days_since_return"],
                top_n=5,
            )
            from app.services.diagnosis_provider import _deterministic_explanation, _enrich_candidate_actions
            candidates = []
            for sc in scored:
                actions = _enrich_candidate_actions(sc.disease)
                candidates.append(
                    DifferentialDiagnosisItem(
                        disease=sc.disease,
                        score=round(sc.score, 3),
                        supporting_findings=sc.supporting_findings,
                        missing_expected_findings=sc.missing_expected_findings,
                        contradicting_information=sc.contradicting_information,
                        uncertainty=sc.uncertainty,
                        explanation_reference=_deterministic_explanation(sc, fields["days_since_return"], fields["countries_visited"]),
                        immediate_tests=actions["immediate_tests"],
                        recommended_investigations=actions["recommended_investigations"],
                        recommended_medications=actions["recommended_medications"],
                        first_line_treatment=actions["first_line_treatment"],
                    )
                )
            from app.schemas.diagnosis import DifferentialDiagnosisResponse
            response = DifferentialDiagnosisResponse(
                consultation_id=str(consultation_id),
                status="SUCCESS",
                message="Deterministic fallback (fast mode — timeout on full analysis)",
                missing_critical_info=[],
                provider_metadata={"provider": "DeterministicFastFallback", "version": "3.0"},
                top_candidates=candidates,
            )
        else:
            from app.schemas.diagnosis import DifferentialDiagnosisResponse
            response = DifferentialDiagnosisResponse(
                consultation_id=str(consultation_id),
                status="INSUFFICIENT_INFO",
                message="No clinical data found and no symptoms provided. Use the 'symptoms' parameter or add intake data.",
                missing_critical_info=["At least one symptom is required"],
                provider_metadata={"provider": "TimeoutFallback"},
                top_candidates=[],
            )

    # Safety evaluation (only if we have candidates)
    if response.top_candidates:
        try:
            for item in response.top_candidates[:3]:  # Limit to top 3 for speed
                safety_decision = await asyncio.wait_for(
                    safety_engine.evaluate_differential_item(db, item, rep),
                    timeout=3.0,
                )
                item.safety_decision = safety_decision
        except Exception:
            pass  # Safety eval failure should not block the response

    return response


# ---------------------------------------------------------------------------
# Sub-30ms Real-Time Clinical Prediction Endpoints
# ---------------------------------------------------------------------------

class RealtimePredictionRequest(BaseModel):
    symptoms: str
    negated_symptoms: Optional[List[str]] = None
    travel_history: Optional[List[str]] = None
    days_since_return: Optional[int] = None
    consultation_id: Optional[uuid.UUID] = None

class RealtimePredictionCandidateItem(BaseModel):
    disease: str
    score: float
    display_score: str
    supporting_findings: List[str] = []
    missing_cardinal_symptoms: List[str] = []
    contradicting_information: List[str] = []
    uncertainty: str = "Moderate"
    icd10: str = ""
    icd11: str = ""
    category: str = ""
    severity: str = "moderate"
    triage: str = "ROUTINE"
    is_hallmark_match: bool = False
    pathognomonic_features: List[str] = []
    immediate_tests: List[str] = []
    recommended_investigations: List[str] = []
    recommended_medications: List[str] = []
    treatment_summary: str = ""
    disease_intelligence: Optional[Dict[str, Any]] = None
    pearl: str = ""
    is_open_domain: bool = False


class RealtimeEmergencyAlert(BaseModel):
    is_emergency: bool
    condition: str
    warning: str
    immediate_action: str

class RealtimePredictionResponse(BaseModel):
    status: str
    latency_ms: float
    query_analyzed: str
    consultation_id: Optional[str] = None
    top_candidates: List[RealtimePredictionCandidateItem] = []
    emergency_alert: Optional[RealtimeEmergencyAlert] = None
    syndromic_clusters: List[str] = []
    open_domain_matched: bool = False
    is_unstructured_note: bool = False
    extracted_findings: List[str] = []
    extracted_negated: List[str] = []
    extracted_vitals: Dict[str, Any] = {}
    diagnostic_markers: List[str] = []
    note_summary: Optional[str] = None
    section_breakdown: Optional[Dict[str, str]] = None
    quantitative_labs: Optional[Dict[str, Any]] = None
    calculated_indices: Optional[Dict[str, Any]] = None
    background_history: Optional[List[str]] = None
    differentiating_recommendation: Optional[Dict[str, Any]] = None
    criteria_evaluations: Optional[List[Dict[str, Any]]] = None
    must_not_miss_candidates: Optional[List[Dict[str, Any]]] = None
    bedside_clarifying_questions: Optional[List[Dict[str, Any]]] = None
    comparison_matrix: Optional[List[Dict[str, Any]]] = None
    clinical_mdm_summary: Optional[str] = None


@router.post("/predict-realtime", response_model=RealtimePredictionResponse)
async def predict_realtime_endpoint(
    payload: RealtimePredictionRequest,
    doctor: Optional[Doctor] = Depends(get_optional_doctor_profile),
):
    """
    Sub-30ms Real-Time Clinical Prediction.
    Evaluates multi-factor clinical reasoning, open-domain universal discovery,
    emergency red flags, and priority bedside investigations with zero wait time.
    """
    from app.services.realtime_prediction_service import realtime_prediction_service
    res = realtime_prediction_service.predict(
        symptoms=payload.symptoms,
        negated_symptoms=payload.negated_symptoms,
        travel_history=payload.travel_history,
        days_since_return=payload.days_since_return,
        consultation_id=str(payload.consultation_id) if payload.consultation_id else None,
        top_k=5,
    )
    return res


@router.get("/{consultation_id}/predict-realtime", response_model=RealtimePredictionResponse)
async def predict_realtime_consultation_endpoint(
    consultation_id: uuid.UUID,
    symptoms: str = Query(default="", description="Optional symptoms override or supplement"),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """
    Sub-30ms Real-Time Prediction for an active consultation session.
    Pulls findings from DB with optional realtime typing override.
    """
    from app.services.representation_service import build_clinical_representation
    from app.services.realtime_prediction_service import realtime_prediction_service

    consultation = await db.scalar(select(Consultation).where(Consultation.id == consultation_id))
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    sym_input: str | list[str] = []
    neg_list = []
    countries = []

    # If symptoms query param is provided, pass directly so clinical note parser can analyze it
    if symptoms.strip():
        sym_input = symptoms
    elif consultation.input_text and consultation.input_text.strip():
        sym_input = consultation.input_text
    else:
        rep = await build_clinical_representation(db, consultation_id)
        sym_input = [item.value for item in rep.symptoms if not getattr(item, "negated", False)]
        neg_list = [item.value for item in rep.negations] if rep.negations else []
        if rep.travel_history:
            countries = [item.value for item in rep.travel_history if item.value.lower() != "none"]

    res = realtime_prediction_service.predict(
        symptoms=sym_input,
        negated_symptoms=neg_list,
        travel_history=countries,
        consultation_id=str(consultation_id),
        top_k=5,
    )
    return res



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
    if consultation and consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    rep = await build_clinical_representation(db, consultation_id) if consultation else None
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
    if consultation and consultation.doctor_id != doctor.id:
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
    if consultation and consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    response = await medication_provider.get_medications(db, disease)
    if consultation:
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

    # Fetch findings for FHIR bundle mapping
    findings = []
    try:
        from app.models.clinical import ClinicalFinding
        findings_stmt = select(ClinicalFinding).where(ClinicalFinding.consultation_id == consultation_id)
        findings = (await db.execute(findings_stmt)).scalars().all()
    except Exception:
        pass

    fmt = format.lower().strip()
    if fmt in ("fhir", "fhir-bundle", "fhir_bundle"):
        return export_service.generate_fhir_bundle(consultation, note_data, findings=findings)
    elif fmt in ("fhir-docref", "fhir_docref"):
        return export_service.generate_fhir_document_reference(consultation, note_data)
    elif fmt == "pdf":
        from fastapi import Response
        pdf_bytes = export_service.generate_pdf(consultation, note_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="consultation_{consultation_id}.pdf"'}
        )
    elif fmt in ("markdown", "md"):
        from fastapi import Response
        md_text = export_service.generate_markdown(consultation, note_data)
        return Response(
            content=md_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="consultation_{consultation_id}.md"'}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Supported: 'fhir' (FHIR R4 Bundle), 'fhir-docref', 'pdf', 'markdown'")

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

    if payload.current_medications:
        for cm in payload.current_medications:
            if cm.lower() not in current_meds:
                current_meds.append(cm.lower())

    return await polypharmacy_simulator.simulate(
        proposed_meds=payload.proposed_medications,
        current_meds=current_meds
    )
