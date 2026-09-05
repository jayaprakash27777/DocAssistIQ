"""DocAssistIQ Backend — Generic Repository Base.

Provides a typed, session-aware base class for all data-access objects.
Concrete repositories subclass ``BaseRepository[Model]`` and gain the
standard CRUD operations without writing boilerplate SQL.

Design decisions:
  - The repository receives a live ``AsyncSession`` in its constructor.
    The session lifecycle (begin/commit/rollback) is managed externally
    via the ``atomic()`` context manager in ``database.py``.
  - ``list_paginated`` enforces an explicit ``limit`` cap (default 100)
    to prevent accidental full-table scans in route handlers.
  - ``update`` requires the caller to pass the fully-loaded ORM object.
    Partial updates are handled by mutating attributes directly and then
    calling ``update()``. This keeps the update contract explicit.
  - All methods are async — no synchronous DB operations in route handlers.

Usage::

    class PatientRepository(BaseRepository[Patient]):
        pass  # inherits all standard operations

    async with atomic(session) as tx:
        repo = PatientRepository(tx)
        patient = await repo.create(Patient(name="Jane Smith"))
        found = await repo.get_by_id(patient.id)
"""

from typing import Generic, TypeVar
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import Base

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=Base)  # type: ignore[type-arg]

# Maximum rows returned by list_paginated without an explicit override.
_DEFAULT_LIMIT = 100
_MAX_LIMIT = 1000


class BaseRepository(Generic[T]):
    """Generic async repository for SQLAlchemy ORM models.

    Args:
        session: An active ``AsyncSession``.  The caller is responsible
                 for transaction lifecycle via ``atomic()``.
        model:   The SQLAlchemy mapped class this repository manages.
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self._session = session
        self._model = model

    # --------------------------------------------------------
    # Read operations
    # --------------------------------------------------------

    async def get_by_id(self, record_id: UUID) -> T | None:
        """Return a single record by primary key, or ``None`` if absent."""
        result = await self._session.execute(
            select(self._model).where(self._model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = _DEFAULT_LIMIT,
    ) -> list[T]:
        """Return a page of records ordered by primary key.

        Args:
            skip:  Number of rows to skip (offset).
            limit: Maximum rows to return. Capped at ``_MAX_LIMIT``.
        """
        effective_limit = min(limit, _MAX_LIMIT)
        result = await self._session.execute(
            select(self._model)
            .order_by(self._model.id)  # type: ignore[attr-defined]
            .offset(skip)
            .limit(effective_limit)
        )
        return list(result.scalars().all())

    async def exists(self, record_id: UUID) -> bool:
        """Return ``True`` if a record with the given ID exists."""
        result = await self._session.execute(
            select(func.count()).where(
                self._model.id == record_id  # type: ignore[attr-defined]
            )
        )
        return (result.scalar() or 0) > 0

    async def count(self) -> int:
        """Return the total number of records in the table."""
        result = await self._session.execute(
            select(func.count()).select_from(self._model)
        )
        return result.scalar() or 0

    # --------------------------------------------------------
    # Write operations
    # --------------------------------------------------------

    async def create(self, obj: T) -> T:
        """Persist a new record and return it with server-generated fields.

        The object is added to the current session. The caller must have
        begun a transaction (via ``atomic()``) before calling this method.
        A ``flush()`` is issued so that server-generated values (e.g.
        ``created_at``, auto-increment sequences) are populated before
        the method returns.
        """
        self._session.add(obj)
        await self._session.flush([obj])
        logger.debug("repository_create", model=self._model.__name__)  # type: ignore[attr-defined]
        return obj

    async def update(self, obj: T) -> T:
        """Persist changes to an already-loaded record.

        Mutate the object's attributes before calling this method.
        A ``flush()`` is issued so ``updated_at`` is refreshed before
        the method returns.
        """
        self._session.add(obj)
        await self._session.flush([obj])
        logger.debug("repository_update", model=self._model.__name__)  # type: ignore[attr-defined]
        return obj

    async def delete(self, obj: T) -> None:
        """Remove a record from the database.

        The deletion is staged in the session and written to the database
        on the next ``flush()`` or ``commit()``.
        """
        await self._session.delete(obj)
        await self._session.flush()
        logger.debug("repository_delete", model=self._model.__name__)  # type: ignore[attr-defined]
