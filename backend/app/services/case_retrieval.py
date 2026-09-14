from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.models.patient import PatientSession
from app.models.patient_profile import PatientProfile
from app.infrastructure.ai.factory import get_embedding_provider


async def get_or_create_consultation_embedding(db: AsyncSession, consultation: Consultation) -> list[float]:
    """Generates and saves the vector embedding for a consultation if it doesn't exist."""
    if consultation.clinical_representation_embedding is not None:
        return consultation.clinical_representation_embedding
    
    # Simple representation: combining input text with any existing findings
    # For a real clinical system, this would be a structured summarization.
    findings_text = "\n".join([f"- {cf.concept}: {cf.value} (Negated: {cf.negated})" for cf in consultation.findings]) if consultation.findings else ""
    text_to_embed = f"Input: {consultation.input_text}\nFindings: {findings_text}"
    
    provider = get_embedding_provider()
    vector = await provider.embed(text_to_embed)
    
    consultation.clinical_representation_embedding = vector
    db.add(consultation)
    await db.commit()
    
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
        
    vector = await get_or_create_consultation_embedding(db, consultation)
    
    # 2. Search similar past cases
    # We join with PatientSession and PatientProfile to get non-identifying demographic info
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
        # We explicitly DO NOT return patient_ref, names, or any direct identifiers.
        case_data = {
            "id": str(past_consultation.id),
            "age_group": profile.age_group if profile else None,
            "biological_sex": profile.biological_sex if profile else None,
            "baseline_conditions": profile.baseline_conditions if profile else {},
            "clinical_presentation_summary": past_consultation.input_text[:200] + "..." if len(past_consultation.input_text) > 200 else past_consultation.input_text,
            "status": past_consultation.status,
            "created_at": past_consultation.created_at.isoformat() if past_consultation.created_at else None,
            "warning": "HISTORICAL REFERENCE - VERIFY APPLICABILITY. Information has been de-identified."
        }
        similar_cases.append(case_data)
        
    return similar_cases
