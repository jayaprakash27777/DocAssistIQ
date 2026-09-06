"""DocAssistIQ — Consultation API Endpoints.

Clinical safety:
  All responses include ``is_placeholder=True`` and a visible placeholder
  label in the ``placeholder_response`` field. This field is NOT a
  clinical decision support result.

Endpoints:
  POST /consultations/           — create a new consultation (doctor role)
  GET  /consultations/           — list current user's consultations (paged)
  GET  /consultations/{id}       — retrieve a single consultation by ID
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationSummary,
)
from app.services import consultation_service

router = APIRouter(prefix="/consultations", tags=["Consultations"])

_PAGE_SIZE_DEFAULT = 20
_PAGE_SIZE_MAX = 100


# ── POST /consultations/ ──────────────────────────────────────────────────


@router.post(
    "/",
    response_model=ConsultationResponse,
    status_code=201,
    summary="Submit a new consultation",
    description=(
        "Submit a clinical text input for analysis. "
        "Returns a **placeholder** non-clinical response until real AI "
        "analysis is integrated in a future phase. "
        "The placeholder is permanently labelled "
        "`PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL`."
    ),
    responses=API_RESPONSES,
)
async def create_consultation(
    payload: ConsultationCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    current_user: User = Depends(require_doctor),  # noqa: B008
) -> ConsultationResponse:
    """Create a consultation and return the placeholder response."""
    return await consultation_service.create_consultation(
        user_id=current_user.id,
        payload=payload,
        db=db,
    )


# ── GET /consultations/ ───────────────────────────────────────────────────


@router.get(
    "/",
    response_model=PagedResponse[ConsultationSummary],
    summary="List consultations for the current user",
    description=(
        "Returns a paginated list of the current user's consultations, "
        "sorted newest-first."
    ),
    responses=API_RESPONSES,
)
async def list_consultations(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=_PAGE_SIZE_DEFAULT,
        ge=1,
        le=_PAGE_SIZE_MAX,
        description="Items per page (max 100)",
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    current_user: User = Depends(require_doctor),  # noqa: B008
) -> PagedResponse[ConsultationSummary]:
    """Return paginated consultations for the authenticated user."""
    import math

    items, total = await consultation_service.list_consultations(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        db=db,
    )
    pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    return PagedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


# ── GET /consultations/{id} ───────────────────────────────────────────────


@router.get(
    "/{consultation_id}",
    response_model=ConsultationResponse,
    summary="Retrieve a single consultation",
    description=(
        "Returns the full consultation record including the placeholder response. "
        "Returns 404 if the consultation does not exist or belongs to another user."
    ),
    responses=API_RESPONSES,
)
async def get_consultation(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    current_user: User = Depends(require_doctor),  # noqa: B008
) -> ConsultationResponse:
    """Fetch a consultation by ID (ownership-guarded)."""
    return await consultation_service.get_consultation(
        consultation_id=consultation_id,
        user_id=current_user.id,
        db=db,
    )
