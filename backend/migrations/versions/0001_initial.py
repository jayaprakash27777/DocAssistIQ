"""Initial migration — install PostgreSQL extensions.

Revision ID: 0001
Revises: (none — first migration)
Create Date: 2026-09-05

Installs the three PostgreSQL extensions required by DocAssistIQ:
  - vector    : pgvector — stores and indexes high-dimensional embeddings
                for semantic similarity search (AI features, Phase 8+)
  - pg_trgm   : trigram text similarity for fuzzy clinical term search
  - btree_gin : multi-column GIN indexes on standard B-tree data types

Downgrade note:
  Extensions are deliberately NOT dropped on downgrade. Dropping an
  extension can fail if other schemas or tenants are using it, and it
  requires the SUPERUSER privilege. The ``alembic_version`` table will
  be updated to reflect the base state, but the extensions themselves
  remain installed. This is safe and expected behaviour for PostgreSQL
  extension lifecycle management.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Install required PostgreSQL extensions."""
    # Use IF NOT EXISTS so the migration is idempotent.
    # The extensions are pre-installed by infra/postgres/init.sql on the
    # first container boot, so this migration typically finds them already
    # present. Running it again is safe.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")


def downgrade() -> None:
    """Intentional no-op: extensions are not dropped on downgrade.

    See module docstring for rationale.
    """
