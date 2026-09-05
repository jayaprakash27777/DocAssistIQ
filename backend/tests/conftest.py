"""Pytest fixtures for DocAssistIQ backend tests.

Test isolation strategy
-----------------------
Unit tests (no ``@pytest.mark.integration`` marker):
  - Use an in-memory SQLite database via ``aiosqlite``.
  - Each test function receives a fresh session that is **rolled back**
    after the test completes — developer data is never mutated.
  - Fast: no network, no Docker required.

Integration tests (``@pytest.mark.integration``):
  - Use the real PostgreSQL instance from the Docker Compose stack.
  - Required only for tests that need PostgreSQL-specific features:
    pgvector, Alembic migration paths, advisory locks, etc.
  - The DATABASE_URL must point to a real PostgreSQL instance.
    The CI pipeline sets ``INTEGRATION_DATABASE_URL`` for this purpose.
  - Each integration test also runs inside a transaction that is rolled
    back after the test. This prevents test-to-test data leakage.

Fixture hierarchy (for async unit tests):
  event_loop (session-scoped)
    └── unit_engine (session-scoped)
          └── unit_session (function-scoped) ← rolled back per test

For integration tests, ``int_session`` is used instead of ``unit_session``.
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)

from app.infrastructure.database import Base

# ============================================================
# Pytest markers
# ============================================================

pytest_mark_integration = pytest.mark.integration


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``integration`` marker."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring a live PostgreSQL database",
    )


# ============================================================
# Unit test fixtures (SQLite in-memory)
# ============================================================

SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def unit_engine():
    """Single in-memory SQLite engine for the entire test session."""
    engine = create_async_engine(
        SQLITE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Create all tables defined in Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def unit_session(unit_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test async session backed by SQLite.

    The session wraps a connection that is held open for the lifetime
    of the test. After the test, the connection is rolled back so that
    no data written during the test persists to the next test.
    """
    async with unit_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False, autobegin=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


# ============================================================
# Integration test fixtures (real PostgreSQL)
# ============================================================

_INTEGRATION_URL = os.environ.get(
    "INTEGRATION_DATABASE_URL",
    "postgresql+asyncpg://docassistiq:changeme@127.0.0.1:5434/docassistiq",
)


@pytest_asyncio.fixture
async def int_engine():
    """Per-test async engine connected to the real PostgreSQL instance.

    Uses ``NullPool`` to avoid connection-pool background tasks that
    outlive the per-test asyncio event loop (which would cause
    ``AttributeError: 'NoneType' object has no attribute 'send'``
    during teardown).
    """
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        _INTEGRATION_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def int_session(int_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test async session backed by real PostgreSQL.

    Uses the same rollback-per-test isolation strategy as ``unit_session``.
    """
    async with int_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False, autobegin=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


# ============================================================
# Convenience alias: ``db_session`` maps to unit or integration
# ============================================================


@pytest_asyncio.fixture
async def db_session(unit_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Default DB fixture — points to the unit (SQLite) session.

    Use ``int_session`` directly in tests marked ``@pytest.mark.integration``.
    """
    yield unit_session
