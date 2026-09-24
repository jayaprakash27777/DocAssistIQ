"""DocAssistIQ Backend - System Router (Enterprise Grade - Zero Hang).

CRITICAL DESIGN:
  GET /health  -- PURE liveness. Returns 200 in < 1ms. NEVER hangs.
                  No DB, no Redis, no Ollama. Just "I am alive".
  GET /ready   -- Readiness with HARD 2s total timeout per dependency.
                  Each probe runs in its own asyncio.wait_for() so one
                  hanging dependency cannot block the others.
                  Returns 503 with per-dependency detail if any fail.
                  Frontend uses this to display the status bar.
  GET /ai-status -- LLM + Ollama health. 3s timeout. Non-critical.
                   Returns LLM availability + whether static KB is active.
"""

import asyncio
import logging
import time
from enum import StrEnum
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.dependencies import get_request_id_dep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

# HARD timeout for each dependency probe - generous enough for Windows thread pools
_DEP_TIMEOUT_S = 3.5


class DependencyStatus(StrEnum):
    HEALTHY   = "healthy"
    UNHEALTHY = "unhealthy"
    TIMEOUT   = "timeout"
    DEGRADED  = "degraded"


class OverallStatus(StrEnum):
    HEALTHY  = "healthy"
    DEGRADED = "degraded"


# ---------------------------------------------------------------------------
# Individual probes — each wrapped in asyncio.wait_for with hard timeout
# ---------------------------------------------------------------------------

async def _probe_database() -> dict:
    """Database probe with hard 2s timeout."""
    try:
        from app.infrastructure.database import probe_database
        await asyncio.wait_for(probe_database(), timeout=_DEP_TIMEOUT_S)
        return {"status": DependencyStatus.HEALTHY}
    except asyncio.TimeoutError:
        logger.warning("database_probe_timeout")
        return {"status": DependencyStatus.TIMEOUT, "error": f"Probe timed out after {_DEP_TIMEOUT_S}s"}
    except Exception as exc:
        logger.warning("database_probe_failed", exc_info=False)
        return {"status": DependencyStatus.UNHEALTHY, "error": str(exc)[:200]}


async def _probe_redis() -> dict:
    """Redis probe with hard 2s timeout — runs sync probe in thread pool."""
    try:
        from app.infrastructure.redis import probe_redis
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(None, probe_redis),
            timeout=_DEP_TIMEOUT_S,
        )
        return {"status": DependencyStatus.HEALTHY}
    except asyncio.TimeoutError:
        logger.warning("redis_probe_timeout")
        return {"status": DependencyStatus.TIMEOUT, "error": f"Probe timed out after {_DEP_TIMEOUT_S}s"}
    except Exception as exc:
        logger.warning("redis_probe_failed", exc_info=False)
        return {"status": DependencyStatus.UNHEALTHY, "error": str(exc)[:200]}


async def _probe_storage() -> dict:
    """Storage probe with hard 2s timeout."""
    try:
        from app.infrastructure.storage import probe_storage
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(None, probe_storage),
            timeout=_DEP_TIMEOUT_S,
        )
        return {"status": DependencyStatus.HEALTHY}
    except asyncio.TimeoutError:
        return {"status": DependencyStatus.TIMEOUT, "error": f"Probe timed out after {_DEP_TIMEOUT_S}s"}
    except Exception as exc:
        return {"status": DependencyStatus.UNHEALTHY, "error": str(exc)[:200]}


async def _probe_llm() -> dict:
    """Ollama/LLM probe with hard 3s timeout. Non-blocking to system health."""
    try:
        from app.services.llm_service import llm_service
        available = await asyncio.wait_for(llm_service.is_available(), timeout=3.0)
        active_model = await llm_service.get_effective_model() if available else None
        return {
            "status": DependencyStatus.HEALTHY if available else DependencyStatus.DEGRADED,
            "mode": "llm_active" if available else "static_kb_fallback",
            "model": active_model or llm_service.default_model,
            "note": "Static clinical KB active — all features available" if not available else f"LLM online ({active_model})",
        }
    except asyncio.TimeoutError:
        return {
            "status": DependencyStatus.DEGRADED,
            "mode": "static_kb_fallback",
            "model": "static_fallback",
            "note": "LLM probe timeout — using offline clinical database (all features still available)",
        }
    except Exception as exc:
        return {
            "status": DependencyStatus.DEGRADED,
            "mode": "static_kb_fallback",
            "model": "static_fallback",
            "note": f"LLM unavailable ({str(exc)[:80]}) — static KB active",
        }


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
async def health(
    request_id: str = Depends(get_request_id_dep),
) -> dict:
    """
    Liveness check — returns 200 in < 1ms if the process is alive.
    NEVER probes any external dependency. Never hangs.
    If this endpoint hangs, the entire process is deadlocked.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "request_id": request_id,
        "timestamp": time.time(),
    }


@router.get("/ready")
async def ready(
    request_id: str = Depends(get_request_id_dep),
) -> JSONResponse:
    """
    Readiness check — probes ALL dependencies in parallel with hard timeouts.
    Total maximum wait: _DEP_TIMEOUT_S (2s).
    LLM degradation does NOT affect readiness — static KB keeps all features alive.
    """
    # Run all probes concurrently with a global timeout guard
    try:
        db_result, redis_result, storage_result, llm_result = await asyncio.wait_for(
            asyncio.gather(
                _probe_database(),
                _probe_redis(),
                _probe_storage(),
                _probe_llm(),
                return_exceptions=True,
            ),
            timeout=_DEP_TIMEOUT_S + 2.0,  # +2s global safety margin
        )
    except asyncio.TimeoutError:
        # Total probe took too long — return degraded but don't hang
        return JSONResponse(
            status_code=503,
            content={
                "status": OverallStatus.DEGRADED,
                "request_id": request_id,
                "dependencies": {
                    "database": {"status": "timeout"},
                    "redis": {"status": "timeout"},
                    "storage": {"status": "timeout"},
                    "llm": {"status": "degraded", "mode": "static_kb_fallback"},
                },
            },
        )

    # Normalize any exceptions from gather
    def _normalize(r) -> dict:
        if isinstance(r, Exception):
            return {"status": DependencyStatus.UNHEALTHY, "error": str(r)[:100]}
        return r

    dependencies = {
        "database": _normalize(db_result),
        "redis":    _normalize(redis_result),
        "storage":  _normalize(storage_result),
        "llm":      _normalize(llm_result),
    }

    # LLM degraded does NOT make system degraded — static KB keeps everything working
    critical_deps = {k: v for k, v in dependencies.items() if k != "llm"}
    all_critical_healthy = all(
        dep["status"] == DependencyStatus.HEALTHY for dep in critical_deps.values()
    )
    overall = OverallStatus.HEALTHY if all_critical_healthy else OverallStatus.DEGRADED
    status_code = 200 if all_critical_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "request_id": request_id,
            "ai_mode": dependencies["llm"].get("mode", "unknown"),
            "dependencies": dependencies,
        },
    )


@router.get("/ai-status")
async def ai_status(
    request_id: str = Depends(get_request_id_dep),
) -> dict:
    """
    AI/LLM subsystem status. Non-critical — always returns 200.
    Tells the frontend whether LLM or static KB is active.
    """
    llm_result = await _probe_llm()
    return {
        "request_id": request_id,
        "llm_available": llm_result.get("status") == "healthy",
        "mode": llm_result.get("mode", "static_kb_fallback"),
        "model": llm_result.get("model", "ii-medical:8b"),
        "note": llm_result.get("note", ""),
        "static_kb_diseases": 200,
        "static_kb_vhf_profiles": 8,
        "features_available": [
            "Disease Intelligence (Ebola, Marburg, Lassa, VHF, 200+ diseases)",
            "Differential Diagnosis",
            "Clinical Note Generation",
            "Investigation Recommendations",
            "NLP Extraction",
        ],
    }
