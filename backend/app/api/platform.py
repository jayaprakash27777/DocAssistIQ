"""DocAssistIQ — Core API Platform Primitives.

Provides reusable schemas and helpers for every route in the API:

    - Pagination  : PaginationParams (query), PagedResponse[T] (envelope)
    - Sorting     : SortParams (query), apply_sort() (whitelisted column sort)
    - Filtering   : FilterParams (base model), build_ilike_filter()
    - Validation  : validate_uuid_param(), require_non_empty_string()
    - OpenAPI     : API_RESPONSES (common response docs), openapi_tags

Usage in a route::

    from app.api.platform import (
        PaginationParams, PagedResponse, SortParams,
        apply_sort, paginate, API_RESPONSES,
    )

    @router.get(
        "/items",
        response_model=PagedResponse[ItemResponse],
        responses=API_RESPONSES,
    )
    async def list_items(
        pagination: PaginationParams = Depends(),
        sort: SortParams = Depends(),
        db: AsyncSession = Depends(get_db),
        user: User = Depends(require_doctor),
    ) -> PagedResponse[ItemResponse]:
        query = select(Item)
        query = apply_sort(query, sort, allowed_columns={"name", "created_at"})
        return await paginate(db, query, pagination, row_schema=ItemResponse)

Design decisions:
    - Pages are 1-based (page=1 is the first page).
    - page_size is capped at 100; page must be >= 1.
    - sort_by column names are whitelisted per-route to prevent column enumeration.
    - All filter values are parameterised — no raw SQL concatenation.
    - PagedResponse is generic so mypy/pyright can validate item types.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ValidationError

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=BaseModel)

# ============================================================
# OpenAPI metadata
# ============================================================

#: Tag metadata for the FastAPI app's ``openapi_tags`` list.
openapi_tags: list[dict] = [
    {
        "name": "Authentication",
        "description": "Register, login, logout and profile endpoints.",
    },
    {
        "name": "Admin",
        "description": (
            "Administrative endpoints restricted to the ``admin`` role. "
            "Unauthenticated requests receive 401; doctor-role requests receive 403."
        ),
    },
    {
        "name": "Platform Probe",
        "description": (
            "Internal platform probe endpoints used to verify pagination, sorting, "
            "filtering and error-envelope conventions. Not a user-facing feature."
        ),
    },
    {
        "name": "system",
        "description": "Health, readiness and version endpoints.",
    },
]

#: Common HTTP response descriptions for route ``responses=`` parameters.
#: Use as ``responses={**API_RESPONSES, 201: {"description": "Created"}}``.
API_RESPONSES: dict[int, dict] = {
    400: {
        "description": "Bad Request — malformed input",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "The request body is malformed.",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            }
        },
    },
    401: {
        "description": "Unauthorized — missing or invalid credentials",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Missing or invalid Authorization header",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            }
        },
    },
    403: {
        "description": "Forbidden — insufficient role",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "REQUIRES_DOCTOR_ROLE",
                        "message": "This action requires the 'doctor' role or higher.",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            }
        },
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "The requested resource was not found.",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            }
        },
    },
    422: {
        "description": "Unprocessable Entity — request validation failed",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": (
                            "Request validation failed: "
                            "body.email: value is not a valid email address"
                        ),
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            }
        },
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred. Please try again later.",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            }
        },
    },
}


# ============================================================
# Pagination
# ============================================================


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints.

    Inject as ``pagination: PaginationParams = Depends()`` on list routes.

    Attributes:
        page:       1-based page number (minimum 1).
        page_size:  Number of items per page (1–100, default 20).
    """

    page: int = Field(
        Query(default=1, ge=1, description="1-based page number"),
    )
    page_size: int = Field(
        Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    )

    @property
    def offset(self) -> int:
        """Zero-based row offset for SQL OFFSET clause."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Row limit for SQL LIMIT clause (same as page_size)."""
        return self.page_size


class PagedResponse(BaseModel, Generic[T]):
    """Standard paginated response envelope.

    Every list endpoint returns this shape::

        {
            "items":     [...],   // typed list of items
            "total":     42,      // total matching rows (before pagination)
            "page":      1,       // current 1-based page
            "page_size": 20,      // items per page
            "pages":     3        // total number of pages
        }
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(
        cls,
        *,
        items: list[T],
        total: int,
        pagination: PaginationParams,
    ) -> PagedResponse[T]:
        """Construct a PagedResponse from items and pagination params."""
        pages = max(1, math.ceil(total / pagination.page_size)) if total > 0 else 1
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )


async def paginate(
    session: AsyncSession,
    query: Select,
    pagination: PaginationParams,
    *,
    row_schema: type[T],
) -> PagedResponse[T]:
    """Execute ``query`` with pagination and return a ``PagedResponse``.

    Runs two SQL statements:
      1. ``SELECT count(*) FROM (query)`` — total matching rows
      2. ``query LIMIT page_size OFFSET (page-1)*page_size`` — page items

    Args:
        session:    Active AsyncSession (from ``get_db``).
        query:      SQLAlchemy ``Select`` statement (un-paginated).
        pagination: Pagination parameters from query string.
        row_schema: Pydantic model to validate each row into.

    Returns:
        A fully populated ``PagedResponse[T]``.
    """
    from sqlalchemy import func, select

    # Count total matching rows (wraps original query as subquery)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total: int = total_result.scalar_one()

    # Fetch the current page
    page_query = query.limit(pagination.limit).offset(pagination.offset)
    rows_result = await session.execute(page_query)
    rows = rows_result.scalars().all()

    items = [row_schema.model_validate(row) for row in rows]
    return PagedResponse.build(items=items, total=total, pagination=pagination)


# ============================================================
# Sorting
# ============================================================

_SORT_DIR = Literal["asc", "desc"]


class SortParams(BaseModel):
    """Query parameters for sorting list endpoints.

    Inject as ``sort: SortParams = Depends()`` on list routes.

    Attributes:
        sort_by:  Column name to sort by (validated against route whitelist).
        sort_dir: Sort direction: ``"asc"`` or ``"desc"`` (default ``"asc"``).
    """

    sort_by: str | None = Field(
        Query(default=None, description="Column name to sort by"),
    )
    sort_dir: _SORT_DIR = Field(
        Query(default="asc", description="Sort direction: asc or desc"),
    )


def apply_sort(
    query: Select,
    sort: SortParams,
    *,
    allowed_columns: set[str],
    model,  # SQLAlchemy ORM model class
) -> Select:
    """Apply whitelisted sorting to a SQLAlchemy ``Select`` statement.

    Args:
        query:           Base SELECT query.
        sort:            Parsed sort params from request.
        allowed_columns: Set of column names this route permits sorting by.
        model:           ORM model class whose columns are referenced.

    Returns:
        Query with ``ORDER BY`` applied, or original query if ``sort_by`` is None.

    Raises:
        ValidationError(422): ``sort_by`` is not in ``allowed_columns``.
    """
    if sort.sort_by is None:
        return query

    if sort.sort_by not in allowed_columns:
        allowed = ", ".join(sorted(allowed_columns))
        raise ValidationError(
            f"Invalid sort column '{sort.sort_by}'. "
            f"Allowed columns: {allowed}.",
            code="INVALID_SORT_COLUMN",
        )

    column = getattr(model, sort.sort_by)
    direction = asc(column) if sort.sort_dir == "asc" else desc(column)
    return query.order_by(direction)


# ============================================================
# Filtering
# ============================================================


class FilterParams(BaseModel):
    """Base model for type-safe filter query parameters.

    Subclass this to add endpoint-specific filters::

        class UserFilterParams(FilterParams):
            role: str | None = Field(Query(default=None))

    Inject as ``filters: UserFilterParams = Depends()`` on list routes.
    """


def build_ilike_filter(column, value: str | None):  # type: ignore[return]
    """Return an ``ilike`` clause for a string column, or ``None``.

    Used for case-insensitive substring searches::

        clause = build_ilike_filter(User.email, search_query)
        if clause is not None:
            query = query.where(clause)

    Args:
        column: SQLAlchemy mapped column.
        value:  Search string (``None`` → no filter applied).

    Returns:
        SQLAlchemy ``ilike`` clause or ``None``.
    """
    if value is None or not value.strip():
        return None
    return column.ilike(f"%{value.strip()}%")


# ============================================================
# Validation helpers
# ============================================================


def validate_uuid_param(value: str, *, param_name: str = "id") -> str:
    """Validate that ``value`` is a well-formed UUID string.

    Args:
        value:      The raw string to validate.
        param_name: Name of the path parameter (for error message).

    Returns:
        The original ``value`` unchanged.

    Raises:
        ValidationError(422): The value is not a valid UUID.
    """
    import uuid as _uuid

    try:
        _uuid.UUID(value)
    except ValueError:
        raise ValidationError(  # noqa: B904
            f"'{param_name}' must be a valid UUID, got: '{value}'.",
            code="INVALID_UUID",
        )
    return value


def require_non_empty_string(value: str | None, *, field_name: str) -> str:
    """Validate that ``value`` is a non-empty, non-whitespace string.

    Args:
        value:      String to validate.
        field_name: Name of the field (for error message).

    Returns:
        The stripped string.

    Raises:
        ValidationError(422): Value is None or whitespace-only.
    """
    if not value or not value.strip():
        raise ValidationError(
            f"'{field_name}' must not be empty or whitespace.",
            code="EMPTY_FIELD",
        )
    return value.strip()
