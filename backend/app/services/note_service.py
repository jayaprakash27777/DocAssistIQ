import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.clinical import ClinicalNote
from app.exceptions import NotFoundError, ValidationError
from app.services.embedding_service import generate_and_store_embedding

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
    
    # Generate an embedding for the updated note for semantic search (Phase 36)
    try:
        if isinstance(current_body, dict):
            # Format SOAP body as flat text for embedding
            text_parts = []
            for k, v in current_body.items():
                if isinstance(v, dict) and "text" in v:
                    text_parts.append(f"{k.upper()}: {v['text']}")
                elif isinstance(v, str):
                    text_parts.append(f"{k.upper()}: {v}")
            note_content = "\n\n".join(text_parts)
            
            if note_content.strip():
                await generate_and_store_embedding(
                    db,
                    source_record_id=str(consultation_id),
                    source_record_type="clinical_note",
                    content=note_content
                )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to generate note embedding: {e}")
    
    return note
