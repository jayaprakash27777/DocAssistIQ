"""Consultation table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-06

Creates the ``consultations`` table with:
  - UUID primary key
  - user_id (UUID FK → users.id, CASCADE DELETE)
  - input_text (TEXT, NOT NULL)
  - status (varchar 20, default 'pending')
  - placeholder_response (TEXT, nullable)
  - created_at / updated_at (server-set timestamps)

Indexes:
  - ``ix_consultations_user_created``: composite (user_id, created_at)
    for efficient paged listing newest-first per user.

Downgrade: drops the ``consultations`` table entirely.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consultations",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Primary key (UUID v4, generated at INSERT)",
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
            comment="FK to the submitting clinician (cascade delete)",
        ),
        sa.Column(
            "input_text",
            sa.Text(),
            nullable=False,
            comment="Clinician's raw text input (max 10 000 chars, validated in schema)",
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
            comment="Lifecycle: 'pending' | 'completed' | 'failed'",
        ),
        sa.Column(
            "placeholder_response",
            sa.Text(),
            nullable=True,
            comment="Non-clinical placeholder response (development only).",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Row insertion timestamp (UTC, server-set)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Last modification timestamp (UTC, server-set)",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_consultations_user_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_consultations_user_created",
        "consultations",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_consultations_user_created", table_name="consultations")
    op.drop_table("consultations")
