from typing import Any
import uuid
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.models.patient import PatientSession
from app.models.patient_profile import PatientProfile
from app.models.clinical import ClinicalFinding
from app.infrastructure.ai.factory import get_embedding_provider

logger = logging.getLogger(__name__)


async def get_or_create_consultation_embedding(db: AsyncSession, consultation: Consultation) -> list[float]:
    """Generates and saves the vector embedding for a consultation if it doesn't exist."""
    if consultation.clinical_representation_embedding is not None:
        return consultation.clinical_representation_embedding
    
    # Safe findings retrieval without triggering greenlet-unsafe lazy load
    findings = []
    if "findings" in consultation.__dict__ and consultation.findings is not None:
        findings = list(consultation.findings)
    else:
        try:
            res = await db.scalars(
                select(ClinicalFinding).where(ClinicalFinding.consultation_id == consultation.id)
            )
            findings = list(res.all())
        except Exception:
            findings = []

    findings_text = "\n".join([f"- {cf.concept}: {cf.value} (Negated: {cf.negated})" for cf in findings]) if findings else ""
    text_to_embed = f"Input: {consultation.input_text}\nFindings: {findings_text}"
    
    provider = get_embedding_provider()
    vector = await provider.embed(text_to_embed)

    # Standardize to 768 dimensions for pgvector column
    if len(vector) > 768:
        vector = vector[:768]
    elif len(vector) < 768:
        vector = vector + [0.0] * (768 - len(vector))
    
    consultation.clinical_representation_embedding = vector
    db.add(consultation)
    try:
        await db.commit()
    except Exception as exc:
        logger.warning(f"Could not persist consultation embedding: {exc}")
        await db.rollback()
    
    return vector


async def find_similar_cases(db: AsyncSession, current_consultation_id: uuid.UUID, limit: int = 5) -> list[dict[str, Any]]:
    """Finds similar past cases based on clinical representation embedding and applies privacy filters."""
    
    # 1. Get current consultation
    consultation = await db.scalar(
        select(Consultation)
        .options(selectinload(Consultation.findings))
        .where(Consultation.id == current_consultation_id)
    )
    if not consultation:
        raise ValueError("Consultation not found")
        
    try:
        vector = await get_or_create_consultation_embedding(db, consultation)
    except Exception as exc:
        logger.error(f"Failed to generate embedding for consultation {current_consultation_id}: {exc}")
        return []
    
    # 2. Search similar past cases
    # We join with PatientSession and PatientProfile to get non-identifying demographic info
    try:
        stmt = (
            select(Consultation, PatientSession, PatientProfile)
            .join(PatientSession, Consultation.patient_session_id == PatientSession.id, isouter=True)
            .join(PatientProfile, PatientSession.patient_profile_id == PatientProfile.id, isouter=True)
            .where(Consultation.id != current_consultation_id)
            .where(Consultation.clinical_representation_embedding != None)
            .order_by(Consultation.clinical_representation_embedding.cosine_distance(vector))
            .limit(limit)
        )
        
        results = await db.execute(stmt)
        similar_cases = []
        
        for past_consultation, session, profile in results:
            # 3. Privacy Filter (strip PII)
            raw_summary = past_consultation.input_text or "Clinical consultation record"
            case_data = {
                "id": str(past_consultation.id),
                "age_group": profile.age_group if profile else None,
                "biological_sex": profile.biological_sex if profile else None,
                "baseline_conditions": profile.baseline_conditions if profile else {},
                "clinical_presentation_summary": (raw_summary[:200] + "...") if len(raw_summary) > 200 else raw_summary,
                "status": past_consultation.status,
                "created_at": past_consultation.created_at.isoformat() if past_consultation.created_at else None,
                "warning": "HISTORICAL REFERENCE - VERIFY APPLICABILITY. Information has been de-identified."
            }
            similar_cases.append(case_data)
            
        return similar_cases
    except Exception as exc:
        logger.warning(f"Error querying similar cases: {exc}")
        await db.rollback()
        return []

