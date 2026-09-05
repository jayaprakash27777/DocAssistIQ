"""DocAssistIQ — Auth API Endpoints.

All four auth endpoints are thin route handlers. Business logic lives
entirely in ``app.services.auth_service``.

Security:
  - Passwords are never logged, never returned, never echoed.
  - Error messages for login failures are generic (no enumeration).
  - The ``Authorization: Bearer <token>`` header is parsed here and
    forwarded to the service; the raw token is not stored on the request
    object or in logs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings_dep
from app.infrastructure.database import atomic
from app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

_bearer = HTTPBearer(auto_error=False)


def _extract_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Extract the Bearer token from the Authorization header."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# ============================================================
# POST /auth/register
# ============================================================


@router.post(
    "/register",
    response_model=MeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new clinician account",
    description=(
        "Create a new user account. Returns the created user profile. "
        "Does not automatically issue an access token — use /login after registering."
    ),
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Register a new user."""
    async with atomic(db):
        user = await auth_service.register_user(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            session=db,
        )
    return MeResponse.model_validate(user)


# ============================================================
# POST /auth/login
# ============================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive an access token",
    description=(
        "Authenticate with email and password. Returns a short-lived Bearer token. "
        "Store the token and include it as `Authorization: Bearer <token>` on subsequent requests."
    ),
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> TokenResponse:
    """Authenticate user and issue JWT."""
    user = await auth_service.authenticate_user(
        email=body.email,
        password=body.password,
        session=db,
    )
    token, expires_in, _jti = auth_service.create_access_token(user.id, settings)
    return TokenResponse(
        access_token=token,
        token_type="bearer",  # noqa: S106
        expires_in=expires_in,
    )


# ============================================================
# POST /auth/logout
# ============================================================


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate the current session token",
    description=(
        "Revoke the supplied Bearer token by adding its JTI to the Redis blacklist. "
        "The token will be rejected on all subsequent requests."
    ),
)
async def logout(
    token: str = Depends(_extract_token),
    settings: Settings = Depends(get_settings_dep),
) -> None:
    """Logout — blacklist the current token JTI."""
    await auth_service.logout_user(token=token, settings=settings)


# ============================================================
# GET /auth/me
# ============================================================


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Return the authenticated user's profile",
    description="Returns the profile of the user identified by the supplied Bearer token.",
)
async def me(
    token: str = Depends(_extract_token),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> MeResponse:
    """Return current authenticated user's profile."""
    user = await auth_service.get_current_user(
        token=token,
        session=db,
        settings=settings,
    )
    return MeResponse.model_validate(user)
