"""DocAssistIQ — Doctor Profile Model.

Extends ``User`` with professional identity and verification state.
One-to-one with ``users``; created when a doctor-role user completes
their profile.

Verification state machine:
  pending → verified (admin review)
           → rejected (admin review)
  rejected → pending (re-submission)

Clinical safety: unverified doctors are blocked from creating
patient-identifiable consultations (enforced in service layer, Phase 10+).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class Doctor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Professional profile for a doctor-role user."""

    __tablename__ = "doctors"

    __table_args__ = (
        Index("ix_doctors_user_id", "user_id", unique=True),
        Index("ix_doctors_tenant_id", "tenant_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="One-to-one with users table",
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        comment="Employing organisation (nullable until assigned)",
    )

    # Professional identity
    specialty: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        comment="Medical specialty (e.g. 'Cardiology', 'General Practice')",
    )

    credential_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Medical registration / license number (opaque reference)",
    )

    credential_body: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        comment="Issuing body (e.g. 'GMC', 'NMC', 'MCI')",
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Professional biography (optional)",
    )

    # Verification state machine
    verification_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Verification: 'pending' | 'verified' | 'rejected'",
    )

    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin user who approved/rejected verification",
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Admin-provided reason if verification_status='rejected'",
    )

    def __repr__(self) -> str:
        return (
            f"<Doctor id={self.id} user_id={self.user_id} "
            f"status={self.verification_status!r}>"
        )
