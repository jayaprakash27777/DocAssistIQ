"""DocAssistIQ — Tenant Model.

A tenant represents an organisation (hospital, clinic, practice) that
subscribes to the DocAssistIQ platform. All clinical data is
tenant-scoped; cross-tenant data access is prohibited at the service layer.

Phase 9 note: this is a foundation model. Multi-tenancy enforcement is
wired in later phases. For now the tenant record anchors FK chains and
establishes the retention / provenance metadata pattern.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An organisation subscribed to DocAssistIQ."""

    __tablename__ = "tenants"

    __table_args__ = (
        Index("ix_tenants_slug", "slug", unique=True),
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Display name of the organisation",
    )

    slug: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        comment="URL-safe unique identifier (lowercase, hyphens only)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="active",
        comment="Lifecycle: 'active' | 'suspended' | 'archived'",
    )

    plan: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default="trial",
        comment="Subscription plan: 'trial' | 'standard' | 'enterprise'",
    )

    contact_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
        comment="Primary contact email for the tenant",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True once the tenant organisation has been KYB-verified",
    )

    settings: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON blob for tenant-specific feature flags and preferences",
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug!r} status={self.status!r}>"
