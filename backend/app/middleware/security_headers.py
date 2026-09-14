from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Phase 68: Security Hardening.
    Injects standard security headers to mitigate XSS, Clickjacking, and Enforce TLS.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # HSTS - Enforce HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Content Security Policy (strict API profile)
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        
        return response
