"""make consent_records patient_session_id nullable

Revision ID: f3b891d1234a
Revises: eaaf403c7a08
Create Date: 2026-10-02 20:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f3b891d1234a'
down_revision: Union[str, None] = 'eaaf403c7a08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'consent_records',
        'patient_session_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'consent_records',
        'patient_session_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False
    )
