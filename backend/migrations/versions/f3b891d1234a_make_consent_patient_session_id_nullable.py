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
    op.execute(
        """
        UPDATE consent_records cr
        SET patient_session_id = c.patient_session_id
        FROM consultations c
        WHERE cr.consultation_id = c.id
          AND cr.patient_session_id IS NULL
          AND c.patient_session_id IS NOT NULL;

        UPDATE consent_records
        SET patient_session_id = (SELECT id FROM patient_sessions LIMIT 1)
        WHERE patient_session_id IS NULL;

        DELETE FROM consent_records
        WHERE patient_session_id IS NULL;
        """
    )
    op.alter_column(
        'consent_records',
        'patient_session_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False
    )

