"""add embedding records

Revision ID: a0f487c3738d
Revises: f0eeb11615ba
Create Date: 2026-09-08 20:28:46.928402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = 'a0f487c3738d'
down_revision: Union[str, None] = 'f0eeb11615ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    op.create_table('embedding_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_record_id', sa.String(length=255), nullable=False),
    sa.Column('source_record_type', sa.String(length=100), nullable=False),
    sa.Column('content_hash', sa.String(length=255), nullable=False),
    sa.Column('embedding_model', sa.String(length=100), nullable=False),
    sa.Column('model_version', sa.String(length=100), nullable=False),
    sa.Column('dimensions', sa.Integer(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_embedding_records_content_hash'), 'embedding_records', ['content_hash'], unique=False)
    op.create_index(op.f('ix_embedding_records_source_record_id'), 'embedding_records', ['source_record_id'], unique=False)
    op.create_index(op.f('ix_embedding_records_source_record_type'), 'embedding_records', ['source_record_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_embedding_records_source_record_type'), table_name='embedding_records')
    op.drop_index(op.f('ix_embedding_records_source_record_id'), table_name='embedding_records')
    op.drop_index(op.f('ix_embedding_records_content_hash'), table_name='embedding_records')
    op.drop_table('embedding_records')
    op.execute('DROP EXTENSION IF EXISTS vector;')
