"""DocAssistIQ — Medical Sources Endpoints (Phase 12).

Endpoints:
  GET    /sources/             — List all sources
  POST   /sources/             — Register a new source (Admin only)
  GET    /sources/{id}         — Get source details
  PATCH  /sources/{id}         — Update a source (Admin only)
  POST   /sources/{id}/verify  — Verify a source for production use (Admin only)

Security:
  - Reading sources is available to all authenticated users (Doctors).
  - Mutating sources (create, update, verify) is strictly limited to Admins.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse
from app.authorization import require_admin, require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate
from app.services import source_service

router = APIRouter(prefix="/sources", tags=["Knowledge Base (Sources)"])


@router.get(
    "/",
    response_model=PagedResponse[SourceResponse],
    summary="List medical sources",
    responses=API_RESPONSES,
)
async def list_sources(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(require_doctor),  # Any authed user can list
    db: AsyncSession = Depends(get_db),
) -> PagedResponse[SourceResponse]:
    """Retrieve a paginated list of medical knowledge sources."""
    sources, total = await source_service.list_sources(db, page, page_size)
    pages = max(1, -(-total // page_size))
    return PagedResponse(
        items=[SourceResponse.model_validate(s) for s in sources],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{source_id}",
    response_model=SourceResponse,
    summary="Get source details",
    responses=API_RESPONSES,
)
async def get_source(
    source_id: uuid.UUID,
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Get details of a specific medical source."""
    source = await source_service.get_source(db, source_id)
    return SourceResponse.model_validate(source)


@router.post(
    "/",
    response_model=SourceResponse,
    status_code=201,
    summary="Register a new source",
    description="Registers a new medical knowledge source. Admin only.",
    responses=API_RESPONSES,
)
async def create_source(
    payload: SourceCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Register a new medical knowledge source."""
    source = await source_service.create_source(db, payload, admin.id)
    return SourceResponse.model_validate(source)


@router.patch(
    "/{source_id}",
    response_model=SourceResponse,
    summary="Update a source",
    description="Updates a medical source. Admin only. Modifying license info resets verification status.",
    responses=API_RESPONSES,
)
async def update_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Update a medical source."""
    source = await source_service.update_source(db, source_id, payload, admin.id)
    return SourceResponse.model_validate(source)


@router.post(
    "/{source_id}/verify",
    response_model=SourceResponse,
    summary="Verify source for production",
    description="Marks a source as suitable for production use. Admin only.",
    responses=API_RESPONSES,
)
async def verify_source(
    source_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Verify a medical source."""
    source = await source_service.verify_source(db, source_id, admin.id)
    return SourceResponse.model_validate(source)
