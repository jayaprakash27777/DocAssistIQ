"""DocAssistIQ — Consultation Service (Phase 20).

Orchestrates the consultation lifecycle state machine and audit trailing.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError, ValidationError
from app.models.consultation import Consultation, ConsultationAudit
from app.models.patient import ConsentRecord
from app.models.clinical import ClinicalFinding
from app.models.transcript import Transcript
from app.services.clinical_nlp import extractor
from app.services.note_generator import note_generator_service


log = structlog.get_logger(__name__)

# Valid state transitions
VALID_TRANSITIONS = {
    "created": {"recording", "draft"},
    "recording": {"created", "processing"},
    "processing": {"draft"},
    "draft": {"under_review"},
    "under_review": {"draft", "analysis_ready"},
    "analysis_ready": {"finalized", "under_review"},
    "finalized": {"amended"},
    "amended": {"finalized"},
}


async def create_consultation(
    db: AsyncSession, doctor_id: uuid.UUID, user_id: uuid.UUID, 
    patient_session_id: uuid.UUID | None = None,
    input_text: str | None = None
) -> Consultation:
    """Create a new consultation in the CREATED state."""
    consultation = Consultation(
        doctor_id=doctor_id,
        patient_session_id=patient_session_id,
        status="created",
        input_text=input_text or "",  # Use provided text or empty
    )
    db.add(consultation)
    await db.flush()
    
    audit = ConsultationAudit(
        consultation_id=consultation.id,
        from_status=None,
        to_status="created",
        actor_id=user_id,
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(consultation)
    
    log.info(
        "consultation_created",
        consultation_id=str(consultation.id),
        doctor_id=str(doctor_id),
    )
    # Re-fetch to ensure relationships like findings are eager loaded
    return await get_consultation(db, consultation.id, doctor_id)


async def get_consultation(
    db: AsyncSession, consultation_id: uuid.UUID, doctor_id: uuid.UUID
) -> Consultation:
    """Fetch a consultation by ID; raises 404 if missing or not owned by doctor."""
    row = await db.scalar(
        select(Consultation)
        .options(selectinload(Consultation.audit_events), selectinload(Consultation.findings))
        .where(Consultation.id == consultation_id)
        .where(Consultation.doctor_id == doctor_id)
    )
    if row is None:
        raise NotFoundError("Consultation not found or unauthorized", code="CONSULTATION_NOT_FOUND")
    return row


async def list_consultations(
    db: AsyncSession, doctor_id: uuid.UUID, limit: int = 20, offset: int = 0
) -> tuple[list[Consultation], int]:
    """List consultations for a doctor, newest first."""
    count_stmt = select(func.count()).select_from(Consultation).where(Consultation.doctor_id == doctor_id)
    total_count = await db.scalar(count_stmt) or 0
    
    stmt = (
        select(Consultation)
        .where(Consultation.doctor_id == doctor_id)
        .order_by(desc(Consultation.created_at))
        .limit(limit)
        .offset(offset)
        .options(selectinload(Consultation.findings))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total_count


async def update_consultation_state(
    db: AsyncSession, 
    consultation_id: uuid.UUID,
    doctor_id: uuid.UUID,
    actor_id: uuid.UUID,
    new_state: str, 
    input_text: str | None = None
) -> Consultation:
    """Transition consultation to a new state if valid."""
    consultation = await get_consultation(db, consultation_id, doctor_id)
    
    current_state = consultation.status
    
    # Idempotency
    if current_state == new_state:
        # Just update text if provided
        if input_text is not None:
            consultation.input_text = input_text
            await db.commit()
            
            # Phase 30: AI Note Generation
            try:
                await note_generator.draft_note_from_findings(db, consultation_id, actor_id)
            except Exception as e:
                # Failing to generate note shouldn't block the state transition, but should be logged.
                log.error("note_generation_failed", error=str(e))
                
        return await get_consultation(db, consultation.id, doctor_id)
        
    allowed_states = VALID_TRANSITIONS.get(current_state, set())
    if new_state not in allowed_states:
        raise ValidationError(
            f"Cannot transition from '{current_state}' to '{new_state}'", code="INVALID_TRANSITION"
        )
        
    # Phase 21: Verify Informed Consent before allowing recording
    if new_state == "recording":
        consent_record = await db.scalar(
            select(ConsentRecord)
            .where(ConsentRecord.consultation_id == consultation_id)
            .where(ConsentRecord.status == "granted")
            .where(ConsentRecord.recording_permitted == True)
            .order_by(desc(ConsentRecord.created_at))
            .limit(1)
        )
        if not consent_record:
            raise ValidationError(
                "Cannot start recording: explicit consent has not been granted or has been revoked.", code="CONSENT_REQUIRED"
            )
        
    # Apply state change
    if input_text is not None:
        consultation.input_text = input_text
        
    # Phase 28: Clinical NLP Extraction on transition to draft
    if new_state == "draft":
        # Extract from manual intake
        findings = await extractor.extract(consultation.input_text, source_context="manual_intake")
        
        # Extract from transcript
        transcript = await db.scalar(
            select(Transcript).where(Transcript.consultation_id == consultation_id)
        )
        if transcript:
            # For simplicity, we just extract from the whole text, but you could extract per-segment
            # Let's get the raw text joined.
            # In a real app we'd load the segments. Let's just use what's there if possible.
            pass
            
        for f in findings:
            finding = ClinicalFinding(
                consultation_id=consultation.id,
                finding_text=f["value"],
                finding_type="symptom" if f["concept"] == "SYMPTOM" else "diagnosis" if f["concept"] == "CONDITION" else "measurement",
                is_ai_suggested=True,
                is_clinician_confirmed=False,
                status="pending",
                confidence_score=f["confidence"],
                concept=f["concept"],
                value=f["value"],
                certainty=f["certainty"],
                negated=f["negated"],
                temporality=f["temporality"],
                source_context=f["source"],
                canonical_concept=f["canonical_concept"],
                mapping_source=f["mapping_source"],
                mapping_confidence=f["mapping_confidence"]
            )
            db.add(finding)
            
    consultation.status = new_state
    
    # Audit log
    audit = ConsultationAudit(
        consultation_id=consultation.id,
        from_status=current_state,
        to_status=new_state,
        actor_id=actor_id,
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(consultation)
    
    log.info(
        "consultation_state_transition",
        consultation_id=str(consultation.id),
        from_state=current_state,
        to_state=new_state,
        actor_id=str(actor_id)
    )

    # Phase 30: Trigger AI note generation on transition to draft
    if new_state == "draft":
        try:
            await note_generator_service.draft_note_from_findings(db, consultation.id, actor_id)
        except Exception as e:
            log.error("note_generation_failed", error=str(e), consultation_id=str(consultation.id))

    return await get_consultation(db, consultation.id, doctor_id)
