"""DocAssistIQ — Admin API Endpoints.

Administrative endpoints that require ``admin`` role.
These exist to:
  1. Provide a testable surface for verifying role enforcement
     (i.e. a doctor attempting GET /admin/ping must receive 403).
  2. Serve as the foundation for future admin-only operations.

All endpoints in this module are protected with ``Depends(require_admin)``.
Unauthenticated requests are rejected with 401 before the role check runs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse, PaginationParams, paginate
from app.authorization import require_admin
from app.config import Settings
from app.dependencies import get_db, get_settings_dep
from app.models.user import User
from app.schemas.auth import MeResponse
from app.services import retention_service
from app.infrastructure.storage import get_s3_client

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================
# Response schemas (admin-only views)
# ============================================================


class AdminPingResponse(BaseModel):
    """Response from the admin liveness probe."""

    ok: bool
    message: str


class AdminStatsResponse(BaseModel):
    """Real-time platform metrics for the admin dashboard."""
    total_users: int
    total_doctors: int
    total_admins: int
    total_consultations: int
    pending_verifications: int


# ============================================================
# GET /admin/ping
# ============================================================


@router.get(
    "/ping",
    response_model=AdminPingResponse,
    summary="Admin liveness probe",
    description=(
        "Returns 200 for authenticated admin users. "
        "Returns 403 FORBIDDEN for doctor-role users. "
        "Returns 401 UNAUTHORIZED for unauthenticated requests. "
        "Used in authorization tests to verify role enforcement."
    ),
    responses=API_RESPONSES,
)
async def admin_ping(
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> AdminPingResponse:
    """Admin-only liveness check."""
    return AdminPingResponse(ok=True, message="Admin access confirmed")


# ============================================================
# GET /admin/stats
# ============================================================


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Get real-time admin metrics",
    description="Returns platform-wide metrics such as total users and consultations.",
    responses=API_RESPONSES,
)
async def get_admin_stats(
    _current_admin: User = Depends(require_admin),  # noqa: B008
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    from sqlalchemy import select, func
    from app.models.consultation import Consultation
    from app.models.doctor import Doctor

    # User counts
    users_result = await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    role_counts = {role: count for role, count in users_result.all()}
    
    total_users = sum(role_counts.values())
    total_doctors = role_counts.get("doctor", 0)
    total_admins = role_counts.get("admin", 0)

    # Consultation count
    consultations_count = await db.scalar(select(func.count(Consultation.id))) or 0

    # Pending verifications count
    pending_verifications = await db.scalar(
        select(func.count(Doctor.id)).where(Doctor.verification_status == "pending")
    ) or 0

    return AdminStatsResponse(
        total_users=total_users,
        total_doctors=total_doctors,
        total_admins=total_admins,
        total_consultations=consultations_count,
        pending_verifications=pending_verifications,
    )


# ============================================================
# POST /admin/retention/purge
# ============================================================


class PurgeResponse(BaseModel):
    stats: dict[str, int]


@router.post(
    "/retention/purge",
    response_model=PurgeResponse,
    summary="Trigger retention purge (admin only)",
    description="Deletes data exceeding the configured retention period.",
    status_code=200,
)
async def admin_trigger_purge(
    _current_admin: User = Depends(require_admin),  # noqa: B008
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep)
) -> PurgeResponse:
    """Manually trigger retention service purge."""
    storage = get_s3_client()
    stats = await retention_service.purge_expired_data(db, storage, settings)
    return PurgeResponse(stats=stats)


# ============================================================
# GET /admin/users
# ============================================================


@router.get(
    "/users",
    response_model=PagedResponse[MeResponse],
    summary="List all registered users (admin only)",
    description=(
        "Returns a paginated list of all registered users. "
        "Supports ``page`` and ``page_size`` query parameters (page_size max 100). "
        "Restricted to admin-role accounts. "
        "Passwords and hashes are never included in the response."
    ),
    responses=API_RESPONSES,
)
async def list_users(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    _current_admin: User = Depends(require_admin),  # noqa: B008
    pagination: PaginationParams = Depends(),  # noqa: B008
) -> PagedResponse[MeResponse]:
    """Return paginated list of all registered users (admin-only)."""
    from sqlalchemy import select

    query = select(User)
    return await paginate(db, query, pagination, row_schema=MeResponse)
