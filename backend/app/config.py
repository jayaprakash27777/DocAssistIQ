"""DocAssistIQ Backend — Application Configuration.

Typed settings loaded from environment variables with validation.
Uses pydantic-settings for type-safe configuration management.

Startup validation rules:
  - In non-development environments, the dev placeholder secret key
    is rejected immediately so the process fails fast rather than
    running insecurely.
"""

from functools import lru_cache

from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET_PLACEHOLDER = "dev-secret-key-change-in-production"  # noqa: S105


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DocAssistIQ"
    app_env: str = "development"
    app_version: str = "0.1.0"
    api_version: str = "v1"
    debug: bool = True
    log_level: str = "info"

    # Backend server
    backend_host: str = "0.0.0.0"  # noqa: S104
    backend_port: int = 8000
    backend_secret_key: str = _DEV_SECRET_PLACEHOLDER  # noqa: S105
    backend_cors_origins: str = "http://localhost:3000"

    # Database (PostgreSQL + asyncpg)
    database_url: str = (
        "postgresql+asyncpg://docassistiq:changeme@localhost:5434/docassistiq"
    )
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20

    # Object Storage (MinIO / S3-compatible)
    object_storage_endpoint: str = "http://localhost:9010"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"  # noqa: S105
    object_storage_bucket: str = "docassistiq"
    object_storage_region: str = "us-east-1"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # --------------------------------------------------------
    # Startup validation
    # --------------------------------------------------------

    @model_validator(mode="after")
    def validate_secrets_for_environment(self) -> "Settings":
        """Reject dev placeholder secrets in non-development environments.

        This causes a hard failure at import time so the process never
        starts in an insecure state. The error is logged before the
        process exits so the issue is visible in container logs.
        """
        if (
            self.app_env != "development"
            and self.backend_secret_key == _DEV_SECRET_PLACEHOLDER
        ):
            msg = (
                "BACKEND_SECRET_KEY must be set to a strong random value "
                f"in environment '{self.app_env}'. "
                "The development placeholder is not permitted in production."
            )
            raise ValueError(msg)
        return self

    # --------------------------------------------------------
    # Computed properties
    # --------------------------------------------------------

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """Synchronous PostgreSQL URL for use by Alembic migrations.

        Alembic's env.py cannot use asyncpg (async-only driver). We
        substitute psycopg2 (widely available binary, handles scram-sha-256)
        so migrations work against a standard PostgreSQL docker instance.
        """
        return self.database_url.replace("+asyncpg", "")

    @property
    def api_v1_prefix(self) -> str:
        """The versioned API prefix, e.g. '/api/v1'."""
        return f"/api/{self.api_version}"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
