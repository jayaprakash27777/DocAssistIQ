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

from app.authorization import require_admin
from app.dependencies import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import MeResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================
# Response schemas (admin-only views)
# ============================================================


class AdminPingResponse(BaseModel):
    """Response from the admin liveness probe."""

    ok: bool
    message: str


class UserListResponse(BaseModel):
    """Paginated user list returned by the admin user endpoint."""

    users: list[MeResponse]
    total: int


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
)
async def admin_ping(
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> AdminPingResponse:
    """Admin-only liveness check."""
    return AdminPingResponse(ok=True, message="Admin access confirmed")


# ============================================================
# GET /admin/users
# ============================================================


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all registered users (admin only)",
    description=(
        "Returns a paginated list of all registered users. "
        "Restricted to admin-role accounts. "
        "Passwords and hashes are never included in the response."
    ),
)
async def list_users(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> UserListResponse:
    """Return all registered users (admin-only)."""
    repo = UserRepository(db)
    users = await repo.list_paginated(limit=100, skip=0)
    total = await repo.count()
    return UserListResponse(
        users=[MeResponse.model_validate(u) for u in users],
        total=total,
    )
