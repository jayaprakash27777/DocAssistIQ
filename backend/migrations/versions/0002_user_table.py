"""Initial user table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-06

Creates the ``users`` table with:
  - UUID primary key
  - email (varchar 320, NOT NULL)
  - password_hash (varchar 256, NOT NULL)
  - full_name (varchar 200, NOT NULL)
  - role (varchar 20, default 'doctor')
  - is_active (boolean, default true)
  - is_verified (boolean, default false)
  - created_at / updated_at (server-set timestamps)

Indexes:
  - ``users_email_lower_idx``: unique, case-insensitive lookup via lower(email)

Downgrade: drops the ``users`` table entirely.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False, comment="Primary key (UUID v4, generated at INSERT)"),
        sa.Column("email", sa.String(320), nullable=False, comment="User email address (case-insensitive unique via lower() index)"),
        sa.Column("password_hash", sa.String(256), nullable=False, comment="bcrypt password hash (never serialised in API responses)"),
        sa.Column("full_name", sa.String(200), nullable=False, comment="Clinician full name as displayed in the UI"),
        sa.Column("role", sa.String(20), server_default="doctor", nullable=False, comment="Role: 'doctor' | 'admin'"),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, comment="False = account suspended; login is rejected"),
        sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False, comment="True once email verification is complete (future phase)"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Row insertion timestamp (UTC, server-set)"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Last modification timestamp (UTC, server-set)"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Case-insensitive unique index on email
    op.create_index(
        "users_email_lower_idx",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("users_email_lower_idx", table_name="users")
    op.drop_table("users")
