"""DocAssistIQ Backend — Shared ORM Mixins.

Mixins are small reusable column sets included in ORM model classes
via multiple inheritance. They should not be standalone mapped tables.

Available mixins:
  TimestampMixin  — created_at / updated_at auto-populated columns

Usage::

    from app.infrastructure.database import Base
    from app.infrastructure.models import TimestampMixin

    class Patient(TimestampMixin, Base):
        __tablename__ = "patients"
        id: Mapped[uuid.UUID] = mapped_column(primary_key=True, ...)
        ...

Clinical note: ``updated_at`` is a database-level audit timestamp, not a
clinical record modification log. Full audit history requires a separate
audit table written via the repository layer.
"""

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns to any mapped class.

    Both are managed by the database server (``server_default`` /
    ``onupdate``), not the application. This avoids clock skew between
    application replicas.

    Column semantics:
      ``created_at`` — set once at INSERT time, never updated.
      ``updated_at`` — set at INSERT; updated automatically on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
        comment="Row insertion timestamp (UTC, server-set)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last modification timestamp (UTC, server-set)",
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column to any mapped class.

    The ``id`` column uses ``default=uuid.uuid4`` — a Python-side
    ``ColumnDefault`` applied by SQLAlchemy at INSERT time (not on
    Python instantiation). The value is available after the first
    ``flush()`` within a session.

    To use a specific UUID, pass it explicitly at construction time:
        model = MyModel(id=uuid.uuid4())
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key (UUID v4, generated at INSERT)",
    )
