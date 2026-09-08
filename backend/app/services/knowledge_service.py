"""DocAssistIQ — Knowledge Review Service (Phase 14).

Handles state transitions for knowledge entities (Disease, Symptom, Investigation, Medicine).
Enforces clinical safety approval paths.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.models.audit import AuditLog
from app.models.knowledge import Disease, Investigation, Medicine, Symptom

log = structlog.get_logger(__name__)

KNOWLEDGE_MODELS = {
    "disease": Disease,
    "symptom": Symptom,
    "investigation": Investigation,
    "medicine": Medicine,
}


async def get_knowledge_entity(db: AsyncSession, entity_type: str, entity_id: uuid.UUID) -> Any:
    model = KNOWLEDGE_MODELS.get(entity_type)
    if not model:
        raise ValidationError(f"Unknown knowledge entity type: {entity_type}", code="INVALID_ENTITY_TYPE")

    result = await db.execute(select(model).where(model.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise NotFoundError(f"{entity_type.capitalize()} not found.", code="ENTITY_NOT_FOUND")
    return entity


async def transition_knowledge_status(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
    new_status: str,
    admin_id: uuid.UUID,
    superseded_by_id: uuid.UUID | None = None,
) -> Any:
    """Safely transitions a knowledge entity to a new status (Phase 14 & 15)."""
    VALID_STATUSES = {"PENDING_REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "OUTDATED"}
    
    if new_status not in VALID_STATUSES:
        raise ValidationError(f"Invalid status {new_status}", code="INVALID_STATUS")

    if new_status == "SUPERSEDED" and not superseded_by_id:
        raise ValidationError("Must provide superseded_by_id when marking as SUPERSEDED.", code="MISSING_SUPERSEDED_BY")

    entity = await get_knowledge_entity(db, entity_type, entity_id)

    # State machine rules
    current = entity.status
    if current == new_status:
        return entity

    # PENDING_REVIEW -> APPROVED | REJECTED
    if current == "PENDING_REVIEW" and new_status not in ("APPROVED", "REJECTED"):
        raise ValidationError(f"Cannot transition from {current} to {new_status}", code="INVALID_TRANSITION")

    # APPROVED -> SUPERSEDED | OUTDATED
    if current == "APPROVED" and new_status not in ("SUPERSEDED", "OUTDATED"):
         raise ValidationError(f"Cannot transition from {current} to {new_status}", code="INVALID_TRANSITION")
         
    # Cannot activate rejected/superseded content
    if current in ("REJECTED", "SUPERSEDED", "OUTDATED") and new_status == "APPROVED":
        raise ValidationError(f"Cannot accidentally activate {current} content. Re-ingest instead."
        , code="SAFETY_VIOLATION")

    entity.status = new_status
    
    # Phase 15: Track effective dates and supersession
    from datetime import datetime, timezone
    if new_status == "APPROVED":
        entity.effective_date = datetime.now(timezone.utc).isoformat()
    elif new_status == "SUPERSEDED":
        entity.superseded_by_id = superseded_by_id
    
    db.add(
        AuditLog(
            actor_id=admin_id,
            action=f"knowledge.{entity_type}.reviewed",
            entity_type=f"knowledge_{entity_type}",
            entity_id=entity.id,
            severity="warning" if new_status == "APPROVED" else "info",
            details={"old_status": current, "new_status": new_status, "superseded_by": str(superseded_by_id) if superseded_by_id else None},
        )
    )
    
    await db.commit()
    await db.refresh(entity)
    
    log.info(
        "knowledge_status_transitioned",
        entity_type=entity_type,
        entity_id=str(entity.id),
        admin_id=str(admin_id),
        old_status=current,
        new_status=new_status,
    )
    
    return entity


async def list_pending_knowledge(
    db: AsyncSession,
    entity_type: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Any], int]:
    """Get entities awaiting review."""
    model = KNOWLEDGE_MODELS.get(entity_type)
    if not model:
         raise ValidationError(f"Unknown knowledge entity type: {entity_type}", code="INVALID_ENTITY_TYPE")

    offset = (page - 1) * page_size
    from sqlalchemy import func

    count_r = await db.execute(
        select(func.count())
        .select_from(model)
        .where(model.status == "PENDING_REVIEW")
    )
    total = count_r.scalar_one()

    result = await db.execute(
        select(model)
        .where(model.status == "PENDING_REVIEW")
        .order_by(model.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total
