"""DocAssistIQ Backend — Custom Exception Hierarchy.

Defines a standard set of domain-level exceptions and the
error-envelope schema that every API error response uses.

Frontend contract:
    Every error response body has this exact shape:
    {
        "error": {
            "code":       "<SCREAMING_SNAKE_CASE machine-readable code>",
            "message":    "<human-readable explanation>",
            "request_id": "<UUID echoed from X-Request-ID header>"
        }
    }

Adding a new exception:
    1. Subclass DocAssistIQError (or a more specific subclass).
    2. Set a `default_code` and `status_code` class attribute.
    3. Register a handler in exception_handlers.py (or rely on the
       generic DocAssistIQError handler).
"""

from pydantic import BaseModel

# ============================================================
# Error Envelope — the canonical API error shape
# ============================================================


class ErrorDetail(BaseModel):
    """Detail block inside every error response."""

    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    """Top-level error response body.

    Usage:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="Resource not found",
                    request_id=rid,
                )
            ).model_dump(),
        )
    """

    error: ErrorDetail


# ============================================================
# Exception Hierarchy
# ============================================================


class DocAssistIQError(Exception):
    """Base exception for all application domain errors.

    Attributes:
        message:      Human-readable description (safe to show to API consumers).
        code:         Machine-readable error code for the error envelope.
        status_code:  HTTP status code to use in the response.
    """

    default_code: str = "INTERNAL_ERROR"
    default_status_code: int = 500

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        *,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status_code


class NotFoundError(DocAssistIQError):
    """Resource does not exist."""

    default_code = "NOT_FOUND"
    default_status_code = 404


class ValidationError(DocAssistIQError):  # noqa: N818 (matches HTTP semantics)
    """Request data failed domain-level validation."""

    default_code = "VALIDATION_ERROR"
    default_status_code = 422


class AuthorizationError(DocAssistIQError):
    """Request is not permitted for the current principal."""

    default_code = "FORBIDDEN"
    default_status_code = 403


class AuthenticationError(DocAssistIQError):
    """Request lacks valid credentials."""

    default_code = "UNAUTHORIZED"
    default_status_code = 401


class ConflictError(DocAssistIQError):
    """Action would create a conflicting state."""

    default_code = "CONFLICT"
    default_status_code = 409


class ServiceUnavailableError(DocAssistIQError):
    """A required downstream service is unavailable."""

    default_code = "SERVICE_UNAVAILABLE"
    default_status_code = 503


class RateLimitError(DocAssistIQError):
    """Request rate limit exceeded."""

    default_code = "RATE_LIMITED"
    default_status_code = 429
