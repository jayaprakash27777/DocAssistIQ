"""DocAssistIQ — ClinicalNote and ClinicalFinding Models.

ClinicalNote: a structured narrative note attached to a consultation.
ClinicalFinding: a discrete clinical finding (symptom/sign/measurement)
  extracted from a consultation, AI-suggested or clinician-confirmed.

AI vs clinician state separation (mandatory):
  - ClinicalFinding.ai_suggested / clinician_confirmed are separate fields.
  - ai_suggested is NEVER automatically promoted to clinician_confirmed.
  - Clinician must explicitly confirm/reject each finding.
  - confirmed_by / confirmed_at audit who confirmed and when.

Clinical safety:
  - finding_text is a non-PII description only.
  - All AI-generated content is labelled is_ai_generated=True.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class ClinicalNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A structured narrative note attached to a consultation.

    Versioned: ``version`` increments on each edit. Previous versions
    are preserved in the audit log (AuditLog.entity = 'clinical_note').
    """

    __tablename__ = "clinical_notes"

    __table_args__ = (
        Index("ix_clinical_notes_consultation", "consultation_id"),
    )

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent consultation",
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Clinician who authored this note",
    )

    note_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default="progress",
        comment="'history' | 'examination' | 'progress' | 'discharge' | 'referral'",
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Note text (non-PII narrative; clinician-confirmed content only)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="draft",
        comment="'draft' | 'final' | 'amended' | 'voided'",
    )

    version: Mapped[int] = mapped_column(
        nullable=False,
        server_default="1",
        comment="Monotonically increasing version number",
    )

    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True if this note was AI-drafted (requires clinician review)",
    )

    def __repr__(self) -> str:
        return f"<ClinicalNote id={self.id} type={self.note_type!r} v={self.version}>"


class ClinicalFinding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A discrete clinical finding from a consultation.

    AI-suggested findings are kept separate from clinician-confirmed ones.
    A finding must be explicitly confirmed by a clinician before it is
    treated as part of the clinical record.
    """

    __tablename__ = "clinical_findings"

    __table_args__ = (
        Index("ix_clinical_findings_consultation", "consultation_id"),
        Index("ix_clinical_findings_status", "status"),
    )

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent consultation",
    )

    finding_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Non-PII description of the finding",
    )

    finding_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="'symptom' | 'sign' | 'measurement' | 'diagnosis' | 'risk_factor'",
    )

    # AI vs clinician separation
    is_ai_suggested: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True if this finding was surfaced by AI (not yet clinician-confirmed)",
    )

    is_clinician_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True only when a clinician has explicitly confirmed this finding",
    )

    confirmed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Clinician who confirmed this finding (null if unconfirmed)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="'pending' | 'confirmed' | 'rejected' | 'superseded'",
    )

    confidence_score: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="AI confidence score [0.0–1.0] (null for clinician-entered findings)",
    )

    def __repr__(self) -> str:
        return (
            f"<ClinicalFinding id={self.id} type={self.finding_type!r} "
            f"confirmed={self.is_clinician_confirmed}>"
        )
