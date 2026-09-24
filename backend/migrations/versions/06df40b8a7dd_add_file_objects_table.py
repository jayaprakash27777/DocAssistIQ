"""Add file_objects table

Revision ID: 06df40b8a7dd
Revises: c52ef03ed888
Create Date: 2026-09-06 17:32:57.989463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06df40b8a7dd'
down_revision: Union[str, None] = 'c52ef03ed888'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if 'file_objects' not in insp.get_table_names():
        op.create_table(
            'file_objects',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('owner_id', sa.Uuid(), nullable=False),
            sa.Column('tenant_id', sa.Uuid(), nullable=True),
            sa.Column('object_key', sa.String(length=1024), nullable=False),
            sa.Column('original_filename', sa.String(length=1024), nullable=False),
            sa.Column('mime_type', sa.String(length=127), nullable=False),
            sa.Column('size_bytes', sa.BigInteger(), nullable=False),
            sa.Column('checksum_sha256', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=64), server_default='pending', nullable=False),
            sa.Column('scan_status', sa.String(length=64), server_default='pending', nullable=False),
            sa.Column('linked_entity_type', sa.String(length=64), nullable=True),
            sa.Column('linked_entity_id', sa.Uuid(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('object_key', name='uq_file_objects_object_key')
        )
        op.create_index(op.f('ix_file_objects_owner_id'), 'file_objects', ['owner_id'], unique=False)
        op.create_index(op.f('ix_file_objects_tenant_id'), 'file_objects', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_file_objects_tenant_id CASCADE")
    op.execute("DROP INDEX IF EXISTS ix_file_objects_owner_id CASCADE")
    op.drop_table('file_objects')
