import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.patient import PatientSession, ConsentRecord
from app.models.consultation import Consultation, ConsultationAudit
from app.models.clinical import ClinicalFinding

async def get_patient_timeline(
    db: AsyncSession,
    patient_profile_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    filters: List[str] = None  # type: ignore
) -> List[Dict[str, Any]]:
    """
    Fetch a chronological timeline of events for a specific patient.
    Aggregates events across Consultations, ClinicalFindings, ConsentRecords, and ConsultationAudits.
    """
    events = []
    
    # We need to find all sessions for this patient
    sessions_stmt = select(PatientSession.id).where(PatientSession.patient_profile_id == patient_profile_id)
    session_ids = (await db.execute(sessions_stmt)).scalars().all()
    
    if not session_ids:
        return []
        
    # Get Consultations
    consultations_stmt = select(Consultation).where(Consultation.patient_session_id.in_(session_ids))
    consultations = (await db.execute(consultations_stmt)).scalars().all()
    consultation_ids = [c.id for c in consultations]
    
    if not consultation_ids:
        return []

    # 1. Add Consultation Events (creation)
    if not filters or "consultation" in filters:
        for c in consultations:
            events.append({
                "id": str(c.id),
                "type": "consultation",
                "timestamp": c.created_at,
                "title": "Consultation Created",
                "description": c.input_text[:100] + "..." if c.input_text else "New consultation started.",
                "status": c.status,
                "consultation_id": str(c.id)
            })
            
    # 2. Add Clinical Findings (only confirmed ones)
    if not filters or "diagnosis" in filters:
        findings_stmt = select(ClinicalFinding).where(
            ClinicalFinding.consultation_id.in_(consultation_ids),
            ClinicalFinding.status == 'confirmed'
        )
        findings = (await db.execute(findings_stmt)).scalars().all()
        for f in findings:
            events.append({
                "id": str(f.id),
                "type": "diagnosis",
                "timestamp": f.updated_at or f.created_at,
                "title": f"Confirmed Finding: {f.value}",
                "description": f"Type: {f.finding_type}. Concept: {f.concept or 'Unknown'}",
                "consultation_id": str(f.consultation_id)
            })

    # 3. Add Consent Records
    if not filters or "consent" in filters:
        consents_stmt = select(ConsentRecord).where(ConsentRecord.consultation_id.in_(consultation_ids))
        consents = (await db.execute(consents_stmt)).scalars().all()
        for consent_record in consents:
            events.append({
                "id": str(consent_record.id),
                "type": "consent",
                "timestamp": consent_record.created_at,
                "title": "Consent Granted" if consent_record.status == "granted" else "Consent Revoked",
                "description": f"By {consent_record.actor_name} ({consent_record.actor_relationship}). Permitted: {consent_record.recording_permitted}",
                "status": consent_record.status,
                "consultation_id": str(consent_record.consultation_id)
            })
            
    # 4. Add Consultation State Transitions (e.g., finalized, amended)
    if not filters or "consultation" in filters:
        audits_stmt = select(ConsultationAudit).where(
            ConsultationAudit.consultation_id.in_(consultation_ids),
            ConsultationAudit.to_status.in_(["finalized", "amended"])
        )
        audits = (await db.execute(audits_stmt)).scalars().all()
        for a in audits:
            events.append({
                "id": str(a.id),
                "type": "consultation",
                "timestamp": a.created_at,
                "title": f"Consultation {a.to_status.capitalize()}",
                "description": f"Status changed from {a.from_status} to {a.to_status}.",
                "consultation_id": str(a.consultation_id)
            })

    # Sort all events chronologically (newest first)
    events.sort(key=  # type: ignore
            lambda x: x["timestamp"] if x["timestamp"] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)  # type: ignore
    
    # Format timestamps
    for e in events:
        e["timestamp"] = e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else None
        
    # Apply pagination manually after aggregating
    return events[offset:offset + limit]
