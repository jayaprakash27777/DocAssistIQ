"""DocAssistIQ Backend — API v1 Root Router.

All versioned business-logic routes are registered here.
Future phases add routers as:
    api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
    api_v1_router.include_router(patients.router, prefix="/patients")

This module deliberately stays thin — it is a registry, not a handler.
"""

from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_request_id_dep, get_settings_dep

api_v1_router = APIRouter(prefix="/api/v1")


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
