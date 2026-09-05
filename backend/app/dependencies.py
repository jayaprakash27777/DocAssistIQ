"""DocAssistIQ Backend — FastAPI Dependency Injection Foundation.

Provides typed `Depends` callables that all routes will import.
Each dependency is self-documenting, testable, and mockable in isolation.

Usage in route functions::

    from app.dependencies import get_db, get_current_user
    from app.authorization import require_doctor, require_admin  # role guards

    @router.get("/patients/{pid}")
    async def get_patient(
        pid: UUID,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(require_doctor),
    ) -> ...:
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.middleware.request_id import get_request_id

if TYPE_CHECKING:
    from app.models.user import User

# ============================================================
# Settings dependency
# ============================================================


async def get_settings_dep() -> Settings:
    """Return the cached application settings.

    Wraps the lru_cache singleton so it can be overridden in tests
    via FastAPI's dependency override mechanism.
    """
    return get_settings()


# ============================================================
# Request correlation ID dependency
# ============================================================


async def get_request_id_dep() -> str:
    """Return the current request's correlation ID.

    This is a thin FastAPI wrapper around the ContextVar accessor
    so routes can declare it as a typed dependency and tests can
    override it without touching middleware.
    """
    return get_request_id()


# ============================================================
# Database session dependency
# ============================================================


async def get_db() -> AsyncGenerator:  # type: ignore[type-arg]
    """Yield a per-request async database session.

    The session is automatically committed on success and rolled back
    on any exception, then closed when the response is sent.

    Override in tests by replacing this dependency.
    """
    from app.infrastructure.database import get_session_factory

    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============================================================
# Authenticated user dependency
# ============================================================

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
) -> User:  # type: ignore[name-defined]
    """Return the authenticated User from the Bearer token.

    Reusable dependency for all protected endpoints. Decodes and
    verifies the JWT, checks the Redis blacklist (logout revocation),
    and returns the live User ORM object.

    Raises:
        HTTPException(401) — missing header, invalid token, expired, revoked.
        HTTPException(403) — account inactive/suspended.
    """
    from fastapi import HTTPException, status

    from app.services import auth_service

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await auth_service.get_current_user(
        token=credentials.credentials,
        session=db,
        settings=settings,
    )


# ============================================================
# Authorization dependencies
# ============================================================
# Import from app.authorization — NOT re-exported here to avoid a circular
# import.  Route modules should import directly:
#   from app.authorization import require_doctor, require_admin


