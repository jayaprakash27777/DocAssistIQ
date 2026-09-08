"""DocAssistIQ — Consultation ORM Model.

Represents a single clinical consultation session submitted by a clinician.
The ``placeholder_response`` field holds the non-clinical development
placeholder. It will be replaced by a real AI response in a future phase.

Clinical safety notes:
  - ``placeholder_response`` is always prefixed with the mandatory label
    ``PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL``.
  - ``input_text`` is stored verbatim; it must never contain patient-
    identifiable data in test or development fixtures.
  - ``status`` tracks the lifecycle: pending → completed | failed.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class Consultation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A clinical text-input consultation submitted by a doctor."""

    __tablename__ = "consultations"

    __table_args__ = (
        # Primary query pattern: list a doctor's consultations newest-first
        Index("ix_consultations_doctor_created", "doctor_id", "created_at"),
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK to the submitting doctor",
    )

    patient_session_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patient_sessions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="FK to the patient session",
    )

    input_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Clinician's raw text input (max 10 000 chars, validated in schema)",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="created",
        comment="Lifecycle: created|recording|processing|draft|under_review|analysis_ready|finalized|amended",
    )

    placeholder_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment=(
            "Non-clinical placeholder response (development only). "
            "Always prefixed with the mandatory safety label."
        ),
    )

    # Relationships
    audit_events: Mapped[list[ConsultationAudit]] = relationship(
        "ConsultationAudit",
        back_populates="consultation",
        cascade="all, delete-orphan",
        order_by="ConsultationAudit.created_at",
    )

    findings: Mapped[list["ClinicalFinding"]] = relationship(
        "ClinicalFinding",
        back_populates="consultation",
        cascade="all, delete-orphan",
        order_by="ClinicalFinding.created_at",
    )

    def __repr__(self) -> str:
        return f"<Consultation id={self.id} status={self.status!r}>"


class ConsultationAudit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Audit log for consultation state transitions."""

    __tablename__ = "consultation_audits"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    actor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="User who triggered the transition",
    )

    consultation: Mapped[Consultation] = relationship("Consultation", back_populates="audit_events")
