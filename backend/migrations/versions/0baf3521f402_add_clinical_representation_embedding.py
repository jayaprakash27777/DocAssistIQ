"""add_clinical_representation_embedding

Revision ID: 0baf3521f402
Revises: ed896898f8a8
Create Date: 2026-09-12 00:33:15.769934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '0baf3521f402'
down_revision: Union[str, None] = 'ed896898f8a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    # Add the column (768 dimensions matching local nomic-embed-text)
    op.add_column('consultations', sa.Column('clinical_representation_embedding', pgvector.sqlalchemy.Vector(768), nullable=True))


def downgrade() -> None:
    op.drop_column('consultations', 'clinical_representation_embedding')
