"""DocAssistIQ Backend — FastAPI Application Entry Point.

Minimal application factory for Phase 0. Provides a health endpoint
and basic CORS configuration. Additional routers, middleware, and
dependencies will be added in subsequent phases.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description="Evidence-grounded Clinical Decision Support API",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint
    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Application health check."""
        return {"status": "healthy", "service": settings.app_name}

    return application


app = create_app()
