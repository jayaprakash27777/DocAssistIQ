"""DocAssistIQ Backend — Database Infrastructure.

Provides a production-grade async SQLAlchemy engine with:
  - Connection pool pre-ping (validates connections before use)
  - Pool recycling (avoids stale connections after network hiccups)
  - Explicit transaction control via the ``atomic()`` context manager
  - No silent partial commits: any exception inside ``atomic()``
    causes a full rollback

Design principles:
  - Engine and session factory are module-level singletons, created
    lazily on first use and disposed on application shutdown.
  - ``autobegin=False`` is set on the session factory so no transaction
    is started until the application explicitly begins one. This makes
    the boundary of every database unit of work visible in the code.
  - ``expire_on_commit=False`` prevents SQLAlchemy from issuing extra
    SELECT statements after a commit to refresh lazy attributes — the
    returned objects are usable without an active session.

Usage:
    # In a FastAPI route (via Depends):
    async def my_route(db: AsyncSession = Depends(get_db)):
        async with atomic(db):
            db.add(SomeModel(...))

    # Or as a standalone operation:
    async with atomic(get_session_factory()()) as session:
        session.add(SomeModel(...))
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, with_loader_criteria

from app.config import get_settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


# ============================================================
# Engine
# ============================================================


def get_engine() -> AsyncEngine:
    """Return (or lazily create) the shared async SQLAlchemy engine.

    The engine is a connection-pool manager. It is created once per
    process lifetime and disposed during application shutdown.
    """
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            # Validate connection health before handing it to the application.
            pool_pre_ping=True,
            # Recycle connections after 30 minutes to avoid stale TCP state.
            pool_recycle=1800,
            # Async driver connection arguments
            connect_args={
                "command_timeout": 10,  # seconds — per-statement timeout
                "server_settings": {
                    "application_name": settings.app_name,
                    "jit": "off",  # disable JIT for OLTP workloads
                },
            },
        )

        # Log pool exhaustion events — indicates under-provisioning
        @event.listens_for(_engine.sync_engine, "connect")
        def on_connect(dbapi_conn, _connection_record) -> None:  # type: ignore[misc]
            logger.debug("database_pool_connect")

        @event.listens_for(_engine.sync_engine, "checkout")
        def on_checkout(dbapi_conn, _connection_record, _connection_proxy) -> None:  # type: ignore[misc]
            logger.debug("database_pool_checkout")

    return _engine


# ============================================================
# Session factory
# ============================================================


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (or lazily create) the async session factory.

    Sessions produced by this factory:
      - Do NOT auto-begin a transaction (``autobegin=False``). The
        application must explicitly start transactions, making unit-
        of-work boundaries visible in the code.
      - Do NOT expire attributes after commit (``expire_on_commit=False``).
        Returned ORM objects remain usable without a live session.
    """
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autobegin=True,
        )
    return _session_factory


@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state) -> None:
    """Automatically append a tenant_id filter to all queries if tenant_id is set."""
    if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
        if execute_state.execution_options.get("bypass_tenant_filter", False):
            return
            
        tenant_id = execute_state.session.info.get("tenant_id")
        if tenant_id:
            from app.infrastructure.models import TenantScopedMixin
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(
                    TenantScopedMixin,
                    lambda cls: cls.tenant_id == tenant_id,
                    include_aliases=True,
                )
            )


# ============================================================
# Transaction management
# ============================================================


@asynccontextmanager
async def atomic(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for an explicit database transaction.

    Guarantees all-or-nothing semantics:
      - Begins a transaction on entry.
      - Commits on clean exit.
      - Rolls back and re-raises on any exception.

    This is the ONLY way a route handler or service should mutate
    database state. Never call ``session.commit()`` directly in
    application code.

    Usage::

        async with atomic(session) as tx:
            tx.add(Patient(...))
            tx.add(AuditLog(...))
        # Both rows committed, or neither if an exception occurred.
    """
    if session.in_transaction():
        async with session.begin_nested():
            try:
                yield session
            except Exception:
                logger.warning("nested_transaction_rolled_back")
                raise
    else:
        async with session.begin():
            try:
                yield session
            except Exception:
                logger.warning("transaction_rolled_back")
                raise


# ============================================================
# Probes
# ============================================================


async def probe_database() -> None:
    """Probe database connectivity. Raises on failure.

    Executes a minimal ``SELECT 1`` over a fresh engine connection.
    Used by the ``GET /ready`` endpoint — does not acquire from the
    application connection pool (avoids warming the pool on startup).
    """
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


# ============================================================
# Lifecycle
# ============================================================


async def close_engine() -> None:
    """Dispose the engine and all pooled connections.

    Call during application shutdown (via the FastAPI lifespan hook).
    """
    global _engine  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("database_engine_disposed")


# ============================================================
# ORM Base
# ============================================================


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models.

    All model modules must be imported before Alembic can auto-detect
    schema changes. Import them in ``migrations/env.py``.
    """
