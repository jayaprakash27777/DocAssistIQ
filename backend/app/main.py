"""DocAssistIQ Backend — FastAPI Application Entry Point.

Application factory with:
  - Lifespan events for connection pool setup/teardown
  - System router (/health, /ready)
  - CORS middleware
  - Versioned API prefix (/api/v1)
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import system

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application-level resources across startup and shutdown."""
    # Startup
    logger.info("Starting DocAssistIQ backend...")
    # Infrastructure clients are lazily initialized on first use.
    # Explicit pre-warming is intentionally deferred to avoid blocking
    # container start if a dependency is temporarily unavailable.
    yield

    # Shutdown — gracefully close connection pools
    logger.info("Shutting down DocAssistIQ backend...")
    from app.infrastructure.database import close_engine
    from app.infrastructure.redis import close_async_client

    await close_engine()
    await close_async_client()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description="Evidence-grounded Clinical Decision Support API",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # System endpoints (health + readiness) at root level
    application.include_router(system.router)

    # Future versioned API routes will be mounted at /api/v1
    # application.include_router(api_v1_router, prefix="/api/v1")

    return application


app = create_app()
