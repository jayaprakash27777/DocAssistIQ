"""Alembic migrations environment.

Supports both online (live database) and offline (SQL script) modes.

Key design decisions:
  - Uses the SYNCHRONOUS ``sync_database_url`` (postgresql+pg8000://) for
    Alembic. The async driver (asyncpg) is not supported inside Alembic's
    env.py migration context.
  - Loads all ORM model modules before running autogenerate so Alembic
    can detect the full schema. Add new model module imports below the
    "--- model imports ---" comment as future phases add them.
  - The database URL is read from app.config — never hardcoded here.
"""

import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Load Alembic logging config (from alembic.ini [loggers] section)
# ---------------------------------------------------------------------------
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# ---------------------------------------------------------------------------
# Set the SQLAlchemy URL from application settings
# ---------------------------------------------------------------------------
from app.config import get_settings  # noqa: E402

settings = get_settings()
# Alembic requires a synchronous URL. We keep asyncpg for runtime and
# pg8000 for migrations to avoid installing a C extension (psycopg2).
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

# ---------------------------------------------------------------------------
# Import Base + all model modules so autogenerate sees the full schema.
# Add new model imports here as phases progress:
#   from app.models.patient import Patient          # Phase 5
#   from app.models.medication import Medication    # Phase 6
# ---------------------------------------------------------------------------
from app.infrastructure.database import Base  # noqa: E402

# --- model imports (add new models here as phases progress) ---
from app.models.user import User as _User  # noqa: F401, E402  — registers table with Base.metadata

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Offline mode — generate SQL script without a live connection
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations against a SQL script file (no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — migrate against a live database
# ---------------------------------------------------------------------------


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no pooling in migration context
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # Include schema in comparisons if using non-public schemas
            include_schemas=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
