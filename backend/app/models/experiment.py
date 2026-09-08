"""DocAssistIQ — Experiment Tracking Models (Phase 19).

Foundation for reproducible ML experiments, tracking code, data,
hyperparameters, metrics, and generated artifacts.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, Index, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class MLExperiment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single reproducible ML experiment run.
    """

    __tablename__ = "ml_experiments"

    __table_args__ = (
        Index("ix_ml_experiments_status", "status"),
        Index("ix_ml_experiments_commit", "code_commit"),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Human-readable name (e.g. 'bert-finetune-v2')",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="running",
        comment="'running' | 'completed' | 'failed' | 'aborted'",
    )

    # ── Reproducibility Metadata ──

    code_commit: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Git commit hash used for this run",
    )

    dataset_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Dataset version string (e.g. 'v1.0.0')",
    )

    dataset_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="SHA-256 hash of the dataset used",
    )

    preprocessing_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="1.0",
        comment="Version of the preprocessing/tokenization pipeline",
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Base model (e.g. 'clinical-bert-base')",
    )

    # ── Hyperparameters & Environment ──

    configuration: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Hyperparameters (learning rate, batch size, etc.)",
    )

    random_seed: Mapped[int] = mapped_column(
        Float,
        nullable=False,
        comment="Random seed for framework (PyTorch/TF/NumPy)",
    )

    hardware: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Hardware topology (e.g. '8x A100 80GB')",
    )

    # ── Outputs ──

    execution_duration_sec: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Total runtime in seconds",
    )

    metrics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Recorded metrics (loss, accuracy, F1, etc.)",
    )

    artifact_location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URI to the trained weights/outputs in object storage",
    )

    def __repr__(self) -> str:
        return f"<MLExperiment name={self.name!r} status={self.status!r}>"
