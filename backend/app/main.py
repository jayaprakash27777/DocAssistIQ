"""DocAssistIQ Backend — FastAPI Application Entry Point.

Application factory wiring together all Phase 0–2 components:
  - Structured logging (structlog JSON/pretty)
  - Request ID / Correlation ID middleware
  - CORS middleware
  - Global exception handlers (error envelope)
  - System router (/health, /ready)
  - Versioned API router (/api/v1)
  - Lifespan events (connection pool teardown)
  - OpenAPI metadata
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.exception_handlers import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.request_id import RequestIDMiddleware
from app.routers import system

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application-level resources across startup and shutdown."""
    logger.info("docassistiq_startup", version=application.version)
    yield
    logger.info("docassistiq_shutdown")
    from app.infrastructure.database import close_engine
    from app.infrastructure.redis import close_async_client

    await close_engine()
    await close_async_client()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Configure structured logging before anything else logs.
    configure_logging(
        level=settings.log_level.upper(),
        json_output=not settings.is_development,
    )

    application = FastAPI(
        title=settings.app_name,
        description=(
            "Evidence-grounded Clinical Decision Support API. "
            "All AI suggestions must be reviewed by qualified clinicians."
        ),
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
        # OpenAPI metadata
        contact={"name": "DocAssistIQ Engineering"},
        license_info={"name": "Proprietary"},
        openapi_tags=[
            {"name": "system", "description": "Health, readiness, and diagnostics"},
            {"name": "auth", "description": "Authentication and session management"},
        ],
    )

    # ----------------------------------------------------------------
    # Middleware (outermost first — RequestID must wrap everything)
    # ----------------------------------------------------------------
    # NOTE: FastAPI/Starlette apply middleware in reverse-registration
    # order, so the last one added is the outermost.  We add RequestID
    # last so it wraps all other middleware and catches all exceptions.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Correlation-ID"],
    )
    application.add_middleware(RequestIDMiddleware)

    # ----------------------------------------------------------------
    # Exception handlers
    # ----------------------------------------------------------------
    register_exception_handlers(application)

    # ----------------------------------------------------------------
    # Routers
    # ----------------------------------------------------------------
    # System endpoints at root level (used by Docker health checks)
    application.include_router(system.router)

    # Versioned business-logic API
    application.include_router(api_v1_router)

    return application


app = create_app()
