import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.clinical import ClinicalNote
from app.exceptions import NotFoundError, ValidationError

async def get_clinical_note(db: AsyncSession, consultation_id: uuid.UUID) -> ClinicalNote:
    row = await db.scalar(
        select(ClinicalNote).where(ClinicalNote.consultation_id == consultation_id)
    )
    if not row:
        raise NotFoundError(
            "Clinical note not found for this consultation", code="NOTE_NOT_FOUND"
        )
    return row

async def update_clinical_note(
    db: AsyncSession,
    consultation_id: uuid.UUID,
    actor_id: uuid.UUID,
    body: Dict[str, Any],
    version: int
) -> ClinicalNote:
    note = await get_clinical_note(db, consultation_id)
    
    if note.version != version:
        raise ValidationError(
            "Conflict: Note has been modified by another process. Please refresh.",
            code="OPTIMISTIC_CONCURRENCY_ERROR",
            status_code=409
        )
    
    # If the passed body is a partial dict (from sections), merge with existing
    current_body = dict(note.body) if note.body else {}
    if body:
        current_body.update(body)
        
    note.body = current_body
    note.version += 1
    note.last_edited_by_id = actor_id
    note.is_ai_generated = False  # Any explicit edit by clinician makes it no longer AI generated

    await db.commit()
    await db.refresh(note)
    
    return note
