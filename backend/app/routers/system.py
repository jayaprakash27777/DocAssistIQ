"""DocAssistIQ Backend — System Router.

Provides liveness and readiness endpoints used by:
  - Docker Compose health checks
  - Kubernetes probes (future)
  - The frontend SystemStatus component

Design:
  GET /health  — liveness.  Always 200. Does NOT check dependencies.
                 If this fails, the process is dead and should restart.

  GET /ready   — readiness. Probes all dependencies in parallel.
                 Returns 200 if all healthy, 503 if any are degraded.
                 Each dependency reports its own status and error detail.
                 The frontend polls this to display the system status bar.
"""

import asyncio
import logging
from enum import StrEnum

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.infrastructure.redis import probe_redis
from app.infrastructure.storage import probe_storage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


class DependencyStatus(StrEnum):
    """Status of a single dependency."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class OverallStatus(StrEnum):
    """Overall system readiness status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"


def _probe_redis_sync() -> dict[str, str]:
    """Run the Redis probe and return a status dict."""
    try:
        probe_redis()
        return {"status": DependencyStatus.HEALTHY}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis probe failed: %s", exc)
        return {"status": DependencyStatus.UNHEALTHY, "error": str(exc)}


def _probe_storage_sync() -> dict[str, str]:
    """Run the storage probe and return a status dict."""
    try:
        probe_storage()
        return {"status": DependencyStatus.HEALTHY}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Storage probe failed: %s", exc)
        return {"status": DependencyStatus.UNHEALTHY, "error": str(exc)}


async def _probe_database_async() -> dict[str, str]:
    """Run the database probe and return a status dict."""
    try:
        from app.infrastructure.database import probe_database

        await probe_database()
        return {"status": DependencyStatus.HEALTHY}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database probe failed: %s", exc)
        return {"status": DependencyStatus.UNHEALTHY, "error": str(exc)}


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check — always returns 200 if the process is alive.

    Does not probe any external dependencies. Used by Docker to decide
    whether to restart the container (not whether to send it traffic).
    """
    settings = get_settings()
    return {"status": "healthy", "service": settings.app_name}


@router.get("/ready")
async def ready() -> JSONResponse:
    """Readiness check — probes all external dependencies.

    Returns 200 if all dependencies are healthy.
    Returns 503 if any dependency is unhealthy, with per-dependency detail.

    Each dependency entry:
      { "status": "healthy" | "unhealthy", "error": "..." (only on failure) }
    """
    # Run DB probe (async) and others (sync in thread pool) concurrently
    db_task = _probe_database_async()
    redis_result, storage_result, db_result = await asyncio.gather(
        asyncio.get_event_loop().run_in_executor(None, _probe_redis_sync),
        asyncio.get_event_loop().run_in_executor(None, _probe_storage_sync),
        db_task,
    )

    dependencies = {
        "database": db_result,
        "redis": redis_result,
        "storage": storage_result,
    }

    all_healthy = all(
        dep["status"] == DependencyStatus.HEALTHY for dep in dependencies.values()
    )
    overall = OverallStatus.HEALTHY if all_healthy else OverallStatus.DEGRADED
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "dependencies": dependencies,
        },
    )
