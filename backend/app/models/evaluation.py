"""DocAssistIQ — Evaluation Harness Models (Phase 18).

Tracks repeatable baseline evaluations and machine-readable metrics.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Index, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single execution of the evaluation harness against a specific dataset and model.
    """

    __tablename__ = "evaluation_runs"

    __table_args__ = (
        Index("ix_evaluation_runs_status", "status"),
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="RESTRICT"),
        nullable=False,
        comment="The fixed held-out evaluation dataset used",
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Identifier for the model or baseline being evaluated",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="'pending' | 'running' | 'completed' | 'failed'",
    )

    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # High-level aggregated metrics
    metrics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Aggregated metrics across all records (e.g. F1, precision, recall)",
    )

    # Detailed results
    results: Mapped[list[EvaluationResult]] = relationship(
        "EvaluationResult",
        back_populates="run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<EvaluationRun id={self.id} status={self.status!r}>"


class EvaluationResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Result for a single record within an EvaluationRun.
    """

    __tablename__ = "evaluation_results"

    __table_args__ = (
        Index("ix_eval_results_run_id", "run_id"),
        Index("ix_eval_results_task_type", "task_type"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    run: Mapped[EvaluationRun] = relationship("EvaluationRun", back_populates="results")

    record_identifier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="ID or hash of the evaluated record from the dataset",
    )

    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'extraction' | 'diagnosis' | 'retrieval' | 'safety' | etc.",
    )

    ground_truth: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Expected output from the dataset",
    )

    model_output: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Actual output produced by the model",
    )

    is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="True if model matches ground truth (for exact match tasks)",
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Continuous score [0-1] (e.g. similarity, rouge)",
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="E.g. 'hallucination', 'unsupported claim', 'leakage detected'",
    )

    def __repr__(self) -> str:
        return f"<EvaluationResult task={self.task_type!r} correct={self.is_correct}>"
