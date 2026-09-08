"""DocAssistIQ — Medical Source Service (Phase 12).

Manages the registration and verification of clinical information sources.
Only admins can register or verify sources.
"""

from __future__ import annotations

import datetime
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.audit import AuditLog
from app.models.provenance import Source
from app.schemas.source import SourceCreate, SourceUpdate

log = structlog.get_logger(__name__)


async def list_sources(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Source], int]:
    """Return paginated list of all sources."""
    offset = (page - 1) * page_size
    from sqlalchemy import func

    count_r = await db.execute(select(func.count()).select_from(Source))
    total = count_r.scalar_one()

    result = await db.execute(
        select(Source)
        .order_by(Source.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    sources = list(result.scalars().all())
    return sources, total


async def get_source(db: AsyncSession, source_id: uuid.UUID) -> Source:
    """Get a source by ID."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise NotFoundError(f"Source {source_id} not found.", code="SOURCE_NOT_FOUND")
    return source


async def create_source(
    db: AsyncSession,
    payload: SourceCreate,
    admin_id: uuid.UUID,
) -> Source:
    """Register a new clinical source (Admin only)."""
    # Check for duplicate code
    existing = await db.execute(select(Source).where(Source.code == payload.code))
    if existing.scalar_one_or_none():
        raise ValidationError(f"Source code '{payload.code}' is already registered.", code="DUPLICATE_CODE")

    source = Source(
        code=payload.code,
        organisation=payload.organisation,
        name=payload.name,
        base_url=payload.base_url,
        access_mechanism=payload.access_mechanism,
        data_type=payload.data_type,
        license_info=payload.license_info,
        status="registered",
        is_production_suitable=False,
    )
    
    db.add(source)
    db.add(
        AuditLog(
            actor_id=admin_id,
            action="source.registered",
            entity_type="source",
            entity_id=None,
            severity="info",
            details={"code": payload.code},
        )
    )
    await db.flush()
    await db.refresh(source)
    await db.commit()

    log.info("source_registered", source_id=str(source.id), admin_id=str(admin_id))
    return source


async def update_source(
    db: AsyncSession,
    source_id: uuid.UUID,
    payload: SourceUpdate,
    admin_id: uuid.UUID,
) -> Source:
    """Update a source (Admin only). Resets verification status if license changes."""
    source = await get_source(db, source_id)

    updated_license = False
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "license_info" and getattr(source, field) != value:
            updated_license = True
        setattr(source, field, value)

    # If license terms change, it must be re-verified
    if updated_license:
        source.is_production_suitable = False
        source.status = "registered"
        source.last_verified_at = None

    db.add(
        AuditLog(
            actor_id=admin_id,
            action="source.updated",
            entity_type="source",
            entity_id=source.id,
            severity="info",
            details={"license_reset": updated_license},
        )
    )
    await db.commit()
    await db.refresh(source)
    
    log.info("source_updated", source_id=str(source.id), admin_id=str(admin_id))
    return source


async def verify_source(
    db: AsyncSession,
    source_id: uuid.UUID,
    admin_id: uuid.UUID,
) -> Source:
    """Verify a source for production use (Admin only)."""
    source = await get_source(db, source_id)

    if not source.license_info:
        raise ValidationError("Cannot verify source without license info.", code="MISSING_LICENSE")

    source.is_production_suitable = True
    source.status = "active"
    source.last_verified_at = datetime.datetime.now(datetime.UTC).isoformat()

    db.add(
        AuditLog(
            actor_id=admin_id,
            action="source.verified",
            entity_type="source",
            entity_id=source.id,
            severity="warning",  # Significant clinical safety action
        )
    )
    await db.commit()
    await db.refresh(source)

    log.info("source_verified", source_id=str(source.id), admin_id=str(admin_id))
    return source
