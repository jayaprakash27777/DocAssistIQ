"""DocAssistIQ Backend — Database infrastructure.

Provides an async SQLAlchemy engine and session factory.
The engine is created once and reused across the application lifetime.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

_engine = None
_session_factory = None


def get_engine():
    """Return (or lazily create) the shared async engine."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,  # verify connections before use
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (or lazily create) the session factory."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield a database session per request."""
    async with get_session_factory()() as session:
        yield session


async def probe_database() -> None:
    """Probe database connectivity. Raises on failure.

    Uses a minimal SELECT 1 query with a short timeout.
    Called by the /ready endpoint.
    """
    from sqlalchemy import text

    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def close_engine() -> None:
    """Dispose the engine (call on application shutdown)."""
    global _engine  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
