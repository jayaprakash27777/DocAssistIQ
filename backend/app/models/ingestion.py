"""DocAssistIQ — Knowledge Ingestion Models (Phase 13).

Models tracking the ingestion pipeline state (Source -> Fetch -> Parse -> Validate -> Normalize -> Hash -> Deduplicate -> Version -> Review Queue).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class IngestionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks the background ingestion of knowledge from a Source."""

    __tablename__ = "ingestion_jobs"

    __table_args__ = (
        Index("ix_ingestion_jobs_source", "source_id"),
        Index("ix_ingestion_jobs_status", "status"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    source_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Version string from the source (e.g. 2026AA)",
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default="pending",
        comment="'pending' | 'fetching' | 'parsing' | 'validating' | 'completed' | 'failed'",
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of the retrieved raw artifact",
    )

    raw_artifact_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        comment="Reference to object storage (e.g. MinIO key)",
    )

    validation_result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON output of validation stage (errors, warnings)",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    review_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default="unreviewed",
        comment="'unreviewed' | 'approved' | 'rejected'",
    )

    def __repr__(self) -> str:
        return f"<IngestionJob id={self.id} status={self.status!r}>"
