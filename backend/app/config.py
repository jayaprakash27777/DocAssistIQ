"""DocAssistIQ Backend — Application Configuration.

Typed settings loaded from environment variables with validation.
Uses pydantic-settings for type-safe configuration management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    debug: bool = True
    log_level: str = "info"

    # Backend server
    backend_host: str = "0.0.0.0"  # noqa: S104
    backend_port: int = 8000
    backend_secret_key: str = "dev-secret-key-change-in-production"  # noqa: S105
    backend_cors_origins: str = "http://localhost:3000"

    # Database (used in later phases)
    database_url: str = "postgresql://docassistiq:changeme@localhost:5432/docassistiq"
    database_echo: bool = False

    # Redis (used in later phases)
    redis_url: str = "redis://localhost:6379/0"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"


def get_settings() -> Settings:
    """Create and return application settings instance."""
    return Settings()
