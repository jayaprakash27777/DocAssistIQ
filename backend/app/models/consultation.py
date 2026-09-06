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
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class Consultation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A clinical text-input consultation submitted by a doctor."""

    __tablename__ = "consultations"

    __table_args__ = (
        # Primary query pattern: list a user's consultations newest-first
        Index("ix_consultations_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to the submitting clinician (cascade delete)",
    )

    input_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Clinician's raw text input (max 10 000 chars, validated in schema)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Lifecycle: 'pending' | 'completed' | 'failed'",
    )

    placeholder_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment=(
            "Non-clinical placeholder response (development only). "
            "Always prefixed with the mandatory safety label."
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Consultation id={self.id} user_id={self.user_id} status={self.status!r}>"
        )
