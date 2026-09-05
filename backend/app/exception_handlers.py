"""DocAssistIQ Backend — Global Exception Handlers.

Maps the application exception hierarchy and FastAPI/Pydantic exceptions
to the standard error envelope defined in app.exceptions.

Handler registration order matters — more specific handlers must be
registered before broader ones. This module exports a single function
``register_exception_handlers`` that is called during app construction.

Security guarantees:
  - Unhandled exceptions produce a generic 500 message (no traceback
    in the response body).
  - The full traceback is logged at ERROR level with the request_id
    so it can be correlated in the log aggregator.
  - HTTP 422 (validation) errors include field-level details that
    are safe to return to clients (field paths + messages, no internals).
"""

import logging

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.exceptions import (
    DocAssistIQError,
    ErrorDetail,
    ErrorResponse,
)
from app.middleware.request_id import get_request_id

logger = structlog.get_logger(__name__)
_stdlib_logger = logging.getLogger(__name__)


def _make_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    """Build a JSONResponse using the standard error envelope."""
    rid = get_request_id()
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, request_id=rid)
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the given FastAPI app."""

    # ------------------------------------------------------------------
    # 1. Domain exceptions (DocAssistIQError and subclasses)
    # ------------------------------------------------------------------

    @app.exception_handler(DocAssistIQError)
    async def handle_domain_error(
        request: Request,
        exc: DocAssistIQError,
    ) -> JSONResponse:
        """Convert any DocAssistIQError to a standard error envelope."""
        logger.warning(
            "domain_error",
            code=exc.code,
            status_code=exc.status_code,
            message=exc.message,
        )
        return _make_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
        )

    # ------------------------------------------------------------------
    # 2. Pydantic / FastAPI request validation errors (422)
    # ------------------------------------------------------------------

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Return structured validation errors in the error envelope."""
        # Build a readable summary from Pydantic's error list.
        # Each entry: "body.field_name: message"
        details = "; ".join(
            f"{'.'.join(str(loc_part) for loc_part in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        )
        message = f"Request validation failed: {details}"
        logger.info("validation_error", detail=details)
        return _make_error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message=message,
        )

    # ------------------------------------------------------------------
    # 3. Starlette/FastAPI HTTPExceptions (404, 405, etc.)
    # ------------------------------------------------------------------

    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        """Wrap HTTPException in the standard error envelope."""
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            410: "GONE",
            422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMITED",
            500: "INTERNAL_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        logger.info("http_exception", status_code=exc.status_code, code=code)
        return _make_error_response(
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
        )

    # ------------------------------------------------------------------
    # 4. Unhandled exceptions → 500, no traceback in body
    # ------------------------------------------------------------------

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all for unexpected errors.

        The full traceback is logged at ERROR level so it can be found
        in the log aggregator via request_id. The response body contains
        only a generic message — no internal details are exposed.
        """
        _stdlib_logger.error(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return _make_error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
        )
