"""DocAssistIQ — Transcript ORM Models (Phase 27).

Persists ASR output, tracking raw, processed, and clinician-corrected states.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin, TenantScopedMixin


class Transcript(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Container for a consultation's transcript segments.
    """
    __tablename__ = "transcripts"

    __table_args__ = (
        Index("ix_transcripts_consultation", "consultation_id", unique=True),
    )

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    status: Mapped[str] = mapped_column(
        String(30),
        server_default="recording",
        nullable=False,
        comment="'recording', 'processing', 'ready', 'finalized'"
    )
    
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment",
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.start_time"
    )


class TranscriptSegment(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single diarized utterance.
    Tracks original raw ASR vs clinician-corrected text for auditability.
    """
    __tablename__ = "transcript_segments"

    __table_args__ = (
        Index("ix_transcript_segments_transcript", "transcript_id"),
    )

    transcript_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    transcript: Mapped["Transcript"] = relationship(
        "Transcript",
        back_populates="segments"
    )

    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    
    speaker_label: Mapped[str] = mapped_column(String(50), nullable=True)
    speaker_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    speaker_source: Mapped[str] = mapped_column(String(30), nullable=True, comment="'asr', 'heuristic', 'clinician'")

    # Text versions
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, comment="Immutable original ASR output")
    processed_text: Mapped[str] = mapped_column(Text, nullable=False, comment="Cleaned/formatted output")
    clinician_corrected_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Explicit correction")
    
    is_corrected: Mapped[bool] = mapped_column(
        server_default="false",
        nullable=False
    )
