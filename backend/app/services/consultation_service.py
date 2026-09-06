"""DocAssistIQ — Consultation Service.

Orchestrates consultation lifecycle:
  create  → persist input, generate placeholder response, mark completed
  get     → fetch with ownership guard
  list    → paginated list for a user

Clinical safety:
  The placeholder_response always begins with PLACEHOLDER_LABEL.
  This function is the single source of truth for placeholder content.
  Replacing it with real AI analysis in a future phase requires only
  changing this module — the API shape is unchanged.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.consultation import Consultation
from app.schemas.consultation import (
    PLACEHOLDER_LABEL,
    ConsultationCreate,
    ConsultationResponse,
    ConsultationSummary,
)

log = structlog.get_logger(__name__)

# ── Placeholder generator ─────────────────────────────────────────────────


def _build_placeholder_response(input_text: str) -> str:
    """
    Build a non-clinical placeholder response.

    The first line is ALWAYS the mandatory safety label so the UI can
    detect and render the warning banner regardless of the body content.
    """
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    char_count = len(input_text)
    return (
        f"{PLACEHOLDER_LABEL}\n\n"
        f"Input received: {char_count} character{'s' if char_count != 1 else ''}.\n"
        f"Submitted: {ts}\n\n"
        "This response is a development placeholder. No clinical analysis\n"
        "has been performed. This output must not be used for clinical decisions.\n"
        "It will be replaced by a real AI-assisted analysis in a future phase."
    )


# ── Service functions ─────────────────────────────────────────────────────


async def create_consultation(
    *,
    user_id: uuid.UUID,
    payload: ConsultationCreate,
    db: AsyncSession,
) -> ConsultationResponse:
    """Create a new consultation and generate the placeholder response."""
    consultation = Consultation(
        user_id=user_id,
        input_text=payload.input_text,
        status="pending",
    )
    db.add(consultation)
    await db.flush()  # assign id before generating response

    placeholder = _build_placeholder_response(payload.input_text)
    consultation.placeholder_response = placeholder
    consultation.status = "completed"

    await db.commit()
    await db.refresh(consultation)

    log.info(
        "consultation_created",
        consultation_id=str(consultation.id),
        user_id=str(user_id),
        char_count=len(payload.input_text),
    )

    return _to_response(consultation)


async def get_consultation(
    *,
    consultation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ConsultationResponse:
    """Fetch a consultation by ID; raises 404 if missing or not owned by user."""
    row = await db.get(Consultation, consultation_id)
    if row is None or row.user_id != user_id:
        raise NotFoundError(
            f"Consultation '{consultation_id}' not found or "
            "does not belong to your account.",
            code="CONSULTATION_NOT_FOUND",
        )
    return _to_response(row)


async def list_consultations(
    *,
    user_id: uuid.UUID,
    page: int,
    page_size: int,
    db: AsyncSession,
) -> tuple[list[ConsultationSummary], int]:
    """
    Return a page of consultation summaries for the given user.

    Returns (items, total) so the caller can build PagedResponse.
    """
    base_filter = Consultation.user_id == user_id

    # Total count
    count_q = select(func.count()).select_from(Consultation).where(base_filter)
    total: int = (await db.execute(count_q)).scalar_one()

    # Page fetch
    offset = (page - 1) * page_size
    rows_q = (
        select(Consultation)
        .where(base_filter)
        .order_by(desc(Consultation.created_at))
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(rows_q)).scalars().all()

    summaries = [_to_summary(r) for r in rows]
    return summaries, total


# ── Private helpers ───────────────────────────────────────────────────────


def _to_response(c: Consultation) -> ConsultationResponse:
    return ConsultationResponse(
        id=c.id,
        user_id=c.user_id,
        input_text=c.input_text,
        status=c.status,
        placeholder_response=c.placeholder_response,
        is_placeholder=True,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _to_summary(c: Consultation) -> ConsultationSummary:
    preview = c.input_text[:120]
    if len(c.input_text) > 120:
        preview += "…"
    return ConsultationSummary(
        id=c.id,
        status=c.status,
        is_placeholder=True,
        input_preview=preview,
        created_at=c.created_at,
    )
