"""DocAssistIQ Backend — Request ID / Correlation ID Middleware.

Every inbound request is assigned a unique UUID that:
  1. Is read from the `X-Request-ID` client header (if provided).
  2. Is generated fresh if the client did not supply one.
  3. Is stored in a ContextVar so every log statement emitted during
     the request automatically includes the same ID.
  4. Is echoed back in the `X-Request-ID` and `X-Correlation-ID`
     response headers.

This enables end-to-end tracing from browser console → server log →
without requiring a full distributed tracing backend in early phases.

Security notes:
  - The Authorization header is NEVER read or logged here.
  - Request body is NEVER read here (streaming is not disrupted).
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar stores the request ID for the duration of the request.
# Default value used when accessed outside a request context (e.g. tests).
request_id_ctx: ContextVar[str] = ContextVar(
    "request_id",
    default="no-request-id",
)

HEADER_NAME = "X-Request-ID"
CORRELATION_HEADER = "X-Correlation-ID"


def get_request_id() -> str:
    """Return the current request's correlation ID.

    Safe to call from anywhere within a request context — and from
    tests where no middleware is active (returns the default sentinel).
    """
    return request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response cycle."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Honour client-provided ID or generate one.
        incoming = request.headers.get(HEADER_NAME)
        rid = incoming if incoming and len(incoming) <= 64 else str(uuid.uuid4())

        # Store in ContextVar — visible to all code on this thread/task.
        token = request_id_ctx.set(rid)
        try:
            response: Response = await call_next(request)
        finally:
            # Always reset the ContextVar, even on exception.
            request_id_ctx.reset(token)

        # Attach to both standard headers.
        response.headers[HEADER_NAME] = rid
        response.headers[CORRELATION_HEADER] = rid
        return response
