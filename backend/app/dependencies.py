"""DocAssistIQ Backend — FastAPI Dependency Injection Foundation.

Provides typed `Depends` callables that all routes will import.
Each dependency is self-documenting, testable, and mockable in isolation.

Usage in route functions:
    @router.get("/patients/{pid}")
    async def get_patient(
        pid: UUID,
        db: AsyncSession = Depends(get_db),
        request_id: str = Depends(get_request_id_dep),
        settings: Settings = Depends(get_settings_dep),
    ) -> ...:
        ...
"""

from collections.abc import AsyncGenerator

from app.config import Settings, get_settings
from app.middleware.request_id import get_request_id

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


async def get_db() -> AsyncGenerator:
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
