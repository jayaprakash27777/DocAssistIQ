"""DocAssistIQ — Authentication Service.

Encapsulates all authentication business logic:
  - Password hashing (bcrypt, work factor 12)
  - JWT creation and verification (HS256, python-jose)
  - Token revocation via Redis JTI blacklist
  - Audit event emission via structlog

Security decisions:
  - ``authenticate_user`` always returns the same generic message for
    both "email not found" and "wrong password" to prevent account
    enumeration. The timing difference is mitigated by running bcrypt's
    ``verify()`` against a dummy hash on lookup miss.
  - JTI (JWT ID) is a UUID stored in the token and in Redis with TTL
    equal to the token's remaining lifetime. This keeps the blacklist
    minimal — entries expire automatically.
  - Tokens are never logged. The JTI is logged for audit correlation.
"""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.exceptions import AuthenticationError, AuthorizationError, ConflictError
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)

# CryptContext with bcrypt at work factor 12.
# ``deprecated="auto"`` will transparently re-hash old entries if the
# scheme changes in future (requires a write path — handled in Phase 5).
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# Used for constant-time verification when the email is not found,
# preventing timing-based enumeration.
_DUMMY_HASH = _pwd_context.hash("dummy-value-never-used")

_ALGORITHM = "HS256"
_TOKEN_TYPE = "bearer"


# ============================================================
# Password helpers
# ============================================================


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if ``plain`` matches ``hashed``. Constant-time."""
    return _pwd_context.verify(plain, hashed)


# ============================================================
# JWT helpers
# ============================================================


def _utcnow() -> datetime:
    return datetime.now(UTC)


def create_access_token(
    user_id: uuid.UUID,
    settings: Settings,
) -> tuple[str, int, str]:
    """Create a signed JWT access token.

    Returns:
        (encoded_token, expires_in_seconds, jti)
    """
    jti = str(uuid.uuid4())
    expire_seconds = settings.jwt_access_token_expire_minutes * 60
    expire_at = _utcnow() + timedelta(seconds=expire_seconds)

    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": expire_at,
        "iat": _utcnow(),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)
    return token, expire_seconds, jti


def decode_token(token: str, settings: Settings) -> dict:
    """Decode and verify a JWT. Raises AuthenticationError on any failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise AuthenticationError(
            "Token is invalid or has expired",
            code="INVALID_TOKEN",
        ) from exc

    if payload.get("type") != "access":
        raise AuthenticationError(
            "Token type is not accepted",
            code="INVALID_TOKEN",
        )
    return payload


# ============================================================
# Redis blacklist helpers
# ============================================================


async def _blacklist_jti(jti: str, ttl_seconds: int) -> None:
    """Add JTI to Redis blacklist with TTL = remaining token lifetime."""
    try:
        import redis.asyncio as aioredis

        from app.config import get_settings

        settings = get_settings()
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.setex(f"blacklist:jti:{jti}", ttl_seconds, "1")
        await client.aclose()
        logger.info("token_blacklisted", jti=jti, ttl=ttl_seconds)
    except Exception:  # noqa: BLE001
        # Blacklist write failure is logged but must not crash the logout endpoint.
        # A best-effort approach is acceptable here; tokens are short-lived.
        logger.exception("token_blacklist_write_failed", jti=jti)


async def _is_jti_blacklisted(jti: str) -> bool:
    """Return True if the JTI has been blacklisted (token revoked)."""
    try:
        import redis.asyncio as aioredis

        from app.config import get_settings

        settings = get_settings()
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        value = await client.get(f"blacklist:jti:{jti}")
        await client.aclose()
        return value is not None
    except Exception:  # noqa: BLE001
        # If Redis is unavailable, fail open (allow the token) to avoid
        # locking out all users during a Redis outage.
        # Phase 7 will add a degraded-mode health warning in the UI.
        logger.exception("token_blacklist_read_failed", jti=jti)
        return False


# ============================================================
# Domain operations
# ============================================================


async def register_user(
    *,
    email: str,
    password: str,
    full_name: str,
    session: AsyncSession,
) -> User:
    """Register a new user.

    Raises:
        AppError(409) if the email is already taken.
    """
    repo = UserRepository(session)

    if await repo.email_exists(email):
        raise ConflictError(
            "An account with this email address already exists",
            code="EMAIL_TAKEN",
        )

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    user = await repo.create(user)

    logger.info(
        "user_registered",
        user_id=str(user.id),
        email=email,
    )
    return user


async def authenticate_user(
    *,
    email: str,
    password: str,
    session: AsyncSession,
) -> User:
    """Verify credentials and return the User.

    Always raises the same AppError(401) for wrong email or wrong
    password to prevent account enumeration.
    """
    repo = UserRepository(session)
    user = await repo.get_by_email(email)

    if user is None:
        # Run bcrypt against a dummy hash to equalise timing.
        verify_password(password, _DUMMY_HASH)
        logger.warning("login_failed_unknown_email", email=email)
        raise AuthenticationError(
            "Invalid email or password",
            code="INVALID_CREDENTIALS",
        )

    if not verify_password(password, user.password_hash):
        logger.warning("login_failed_wrong_password", user_id=str(user.id))
        raise AuthenticationError(
            "Invalid email or password",
            code="INVALID_CREDENTIALS",
        )

    if not user.is_active:
        logger.warning("login_rejected_inactive_account", user_id=str(user.id))
        raise AuthorizationError(
            "This account has been suspended. Contact your administrator.",
            code="ACCOUNT_INACTIVE",
        )

    logger.info("login_success", user_id=str(user.id))
    return user


async def logout_user(*, token: str, settings: Settings) -> None:
    """Invalidate a token by blacklisting its JTI in Redis."""
    payload = decode_token(token, settings)
    jti: str = payload["jti"]
    exp: int = payload["exp"]

    remaining_ttl = max(0, int(exp - _utcnow().timestamp()))
    if remaining_ttl > 0:
        await _blacklist_jti(jti, remaining_ttl)


async def get_current_user(
    *,
    token: str,
    session: AsyncSession,
    settings: Settings,
) -> User:
    """Decode the JWT, check the blacklist, and return the live User.

    Raises:
        AppError(401) on any token problem.
        AppError(403) if the user account is inactive.
    """
    payload = decode_token(token, settings)
    jti: str = payload.get("jti", "")
    user_id_str: str = payload.get("sub", "")

    if await _is_jti_blacklisted(jti):
        raise AuthenticationError(
            "This session has been logged out",
            code="TOKEN_REVOKED",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, AttributeError) as exc:
        raise AuthenticationError(
            "Token subject is malformed",
            code="INVALID_TOKEN",
        ) from exc

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if user is None:
        raise AuthenticationError(
            "The user account no longer exists",
            code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise AuthorizationError(
            "This account has been suspended",
            code="ACCOUNT_INACTIVE",
        )

    return user
