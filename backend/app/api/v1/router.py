"""DocAssistIQ Backend — API v1 Root Router.

All versioned business-logic routes are registered here.
Future phases add routers as:
    api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
    api_v1_router.include_router(patients.router, prefix="/patients")

This module deliberately stays thin — it is a registry, not a handler.
"""

from fastapi import APIRouter, Depends

from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.consent import router as consent_router
from app.api.v1.endpoints.consultations import router as consultations_router
from app.api.v1.endpoints.intake import router as intake_router
from app.api.v1.endpoints.transcript import router as transcript_router
from app.api.v1.endpoints.doctors import router as doctors_router
from app.api.v1.endpoints.files import router as files_router
from app.api.v1.endpoints.ingestion import router as ingestion_router
from app.api.v1.endpoints.knowledge import router as knowledge_router
from app.api.v1.endpoints.datasets import router as datasets_router
from app.api.v1.endpoints.evaluation import router as evaluation_router
from app.api.v1.endpoints.experiments import router as experiments_router
from app.api.v1.endpoints.platform_probe import router as probe_router
from app.api.v1.endpoints.sources import router as sources_router
from app.api.v1.endpoints.ws import router as ws_router
from app.api.v1.endpoints.rag import router as rag_router
from app.api.v1.endpoints.verification import router as verification_router
from app.api.v1.endpoints.explanation import router as explanation_router
from app.config import Settings
from app.dependencies import get_request_id_dep, get_settings_dep

api_v1_router = APIRouter(prefix="/api/v1")

# Phase 4 — Authentication
api_v1_router.include_router(auth_router)

# Phase 5 — Authorization (admin probe endpoints)
api_v1_router.include_router(admin_router)

# Phase 6 — Core API Platform (probe endpoint exercises platform primitives)
api_v1_router.include_router(probe_router)

# Phase 8 — Walking Skeleton: consultations vertical slice
api_v1_router.include_router(consultations_router)

# Phase 10 — Doctor Profile and Verification
api_v1_router.include_router(doctors_router)

# Phase 11 — Secure File Storage
api_v1_router.include_router(files_router)

# Phase 12 — Medical Source Registry
api_v1_router.include_router(sources_router)

# Phase 13 — Knowledge Ingestion Framework
api_v1_router.include_router(ingestion_router)

# Phase 14 — Knowledge Review and Publication
api_v1_router.include_router(knowledge_router)

# Phase 17 — Dataset Registry and Governance
api_v1_router.include_router(consent_router)
api_v1_router.include_router(intake_router)
api_v1_router.include_router(transcript_router)
api_v1_router.include_router(datasets_router)

# Phase 18 — Evaluation Harness
api_v1_router.include_router(evaluation_router)

# Phase 19 — Experiment Tracking Foundation
api_v1_router.include_router(experiments_router)

# Phase 37 — RAG Retrieval
api_v1_router.include_router(rag_router)

# Phase 38 — Claim-Level Citation Verification
api_v1_router.include_router(verification_router)

# Phase 39 — Clinical Explanation / Why?
api_v1_router.include_router(explanation_router)

# Phase 8 — WebSocket stream (mounted at app level — see main.py)
# ws_router is imported here and exported for main.py to include directly
__all__ = ["api_v1_router", "ws_router"]



# ------------------------------------------------------------------
# GET /api/v1/ping
# A lightweight "am I talking to the right API?" check.
# Returns version, environment, and the request correlation ID.
# Used by the frontend on app load to confirm API compatibility.
# ------------------------------------------------------------------


@api_v1_router.get(
    "/ping",
    tags=["system"],
    summary="API version check",
    response_description="API version and current environment",
)
async def ping(
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
    request_id: str = Depends(get_request_id_dep),  # noqa: B008
) -> dict[str, str]:
    """Return the API version, environment name, and request correlation ID.

    The frontend calls this once on load to confirm it is connected to
    the expected API version before making business-logic requests.
    """
    return {
        "version": settings.app_version,
        "api_version": settings.api_version,
        "env": settings.app_env,
        "request_id": request_id,
    }
