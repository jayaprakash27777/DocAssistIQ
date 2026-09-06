"""DocAssistIQ — Platform Probe Endpoint.

Exercises every API platform primitive end-to-end against a real database:
  - PaginationParams (page / page_size)
  - PagedResponse[T] envelope
  - SortParams (sort_by / sort_dir) with column whitelist
  - FilterParams (role filter)
  - Correlation ID echoed in X-Request-ID response header

This endpoint is NOT a user-facing product feature. Its sole purpose is
to provide a concrete, testable surface for the platform integration tests
in ``tests/test_platform.py``.

Access requires an authenticated ``doctor`` or ``admin`` account.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import (
    API_RESPONSES,
    FilterParams,
    PagedResponse,
    PaginationParams,
    SortParams,
    apply_sort,
    paginate,
)
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.auth import MeResponse

router = APIRouter(prefix="/probe", tags=["Platform Probe"])

# Columns that callers are allowed to sort on for the user probe.
_USER_SORT_WHITELIST: set[str] = {"email", "full_name", "role", "created_at"}

# Roles that callers are allowed to filter on.
_ALLOWED_ROLES: set[str] = {"doctor", "admin"}


class UserFilterParams(FilterParams):
    """Filter parameters for the user probe endpoint."""

    from fastapi import Query
    from pydantic import Field

    role: str | None = Field(Query(default=None, description="Filter by role (doctor or admin)"))


# ============================================================
# GET /probe/users
# ============================================================


@router.get(
    "/users",
    response_model=PagedResponse[MeResponse],
    summary="Platform probe — paginated, sorted, filtered user list",
    description=(
        "Returns a paginated list of users. "
        "Exercises PaginationParams, SortParams, FilterParams and PagedResponse. "
        "Requires authentication (doctor or admin role). "
        "**Not a user-facing product feature — integration test surface only.**"
    ),
    responses=API_RESPONSES,
)
async def probe_users(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(require_doctor),  # noqa: B008
    pagination: PaginationParams = Depends(),  # noqa: B008
    sort: SortParams = Depends(),  # noqa: B008
    filters: UserFilterParams = Depends(),  # noqa: B008
) -> PagedResponse[MeResponse]:
    """Return a paginated, sorted, filtered list of users.

    This route deliberately reads from the ``users`` table so that platform
    test fixtures can create known users and assert on the paginated output.
    """
    from app.exceptions import ValidationError

    query = select(User)

    # Apply role filter (whitelisted values only)
    if filters.role is not None:
        if filters.role not in _ALLOWED_ROLES:
            raise ValidationError(
                f"Invalid role filter '{filters.role}'. "
                f"Allowed values: {', '.join(sorted(_ALLOWED_ROLES))}.",
                code="INVALID_ROLE_FILTER",
            )
        query = query.where(User.role == filters.role)

    # Apply whitelisted sort
    query = apply_sort(query, sort, allowed_columns=_USER_SORT_WHITELIST, model=User)

    return await paginate(db, query, pagination, row_schema=MeResponse)
