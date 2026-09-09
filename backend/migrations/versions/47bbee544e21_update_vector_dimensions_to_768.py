"""update_vector_dimensions_to_768

Revision ID: 47bbee544e21
Revises: a0f487c3738d
Create Date: 2026-09-09 14:51:12.564388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '47bbee544e21'
down_revision: Union[str, None] = 'a0f487c3738d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('embedding_records', 'embedding',
               existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=1536),
               type_=pgvector.sqlalchemy.vector.VECTOR(dim=768),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('embedding_records', 'embedding',
               existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=768),
               type_=pgvector.sqlalchemy.vector.VECTOR(dim=1536),
               existing_nullable=False)
