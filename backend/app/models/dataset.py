"""DocAssistIQ — Dataset Registry and Governance Models (Phase 17).

Only approved datasets can enter training/evaluation pipelines.
De-identification is mandatory for datasets intended for ML.
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, Index, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class Dataset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A registered dataset for ML training, evaluation, or research.
    
    Data is stored externally (e.g. S3, data/processed/). This model
    tracks the governance, schema, and provenance metadata.
    """

    __tablename__ = "datasets"

    __table_args__ = (
        Index("ix_datasets_name_version", "name", "version", unique=True),
        Index("ix_datasets_approval_status", "approval_status"),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Dataset name (e.g. 'mimic-iv-notes-filtered')",
    )

    source: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Origin of the data (e.g. 'MIMIC-IV v2.2', 'Synthetically generated')",
    )

    license: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Data license (e.g. 'PhysioNet Credentialed', 'Internal Only')",
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Semantic version (e.g. '1.0.0')",
    )

    hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="SHA-256 hash of the dataset file(s) to guarantee immutability",
    )

    schema: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Expected columns, types, and constraints (JSON Schema)",
    )

    validation_rules: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Configured quality checks (e.g., missing values thresholds)",
    )

    record_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default="0",
        comment="Total number of records in the dataset",
    )

    is_deidentified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True if passed the automated PII removal & manual audit",
    )

    approval_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="'pending' | 'approved' | 'rejected' | 'deprecated'",
    )

    intended_use: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Valid purposes (e.g. 'training NLP model X', 'evaluation only')",
    )

    limitations: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Known biases, missing demographics, or quality issues",
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Relative path or URI to the raw/processed files",
    )

    def __repr__(self) -> str:
        return f"<Dataset name={self.name!r} version={self.version!r} status={self.approval_status!r}>"
