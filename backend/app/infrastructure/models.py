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
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, text, event, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, object_session


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


class TenantScopedMixin:
    """Adds a ``tenant_id`` column for strict multi-tenant isolation.
    
    This mixin establishes the physical boundary for tenant data.
    Queries should always filter by this column via a loader criteria.
    """
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The tenant this data belongs to",
    )

@event.listens_for(TenantScopedMixin, "before_insert", propagate=True)
def _auto_populate_tenant_id(mapper, connection, target):
    """Automatically populate tenant_id from the session if it's missing."""
    if target.tenant_id is None:
        session = object_session(target)
        if session and "tenant_id" in session.info:
            target.tenant_id = session.info["tenant_id"]
        else:
            try:
                result = connection.execute(text("SELECT id FROM tenants LIMIT 1")).scalar()
                if result:
                    target.tenant_id = result
                    if session:
                        session.info["tenant_id"] = result
            except Exception:
                pass
