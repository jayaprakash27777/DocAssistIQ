"""DocAssistIQ — Authorization Foundation.

Provides reusable FastAPI dependencies for role-based access control (RBAC).

Usage in route handlers::

    from app.authorization import require_permission
    from app.models.user import User

    @router.get("/clinical-data")
    async def clinical_data(
        user: User = Depends(require_permission("consultation", "read")),
    ) -> ...:
        ...

Security guarantees:
    - Authorization is always checked server-side, independent of any
      frontend visibility control.
    - The role is read from the live ``User`` ORM row returned by
      ``get_current_user``, NOT from the JWT payload.
    - Unauthenticated requests are rejected with 401 before role checking
      even begins (``get_current_user`` raises first).
    - Suspended accounts are rejected with 403 ACCOUNT_INACTIVE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from fastapi import Depends

from app.exceptions import AuthorizationError

if TYPE_CHECKING:
    from app.models.user import User

# ============================================================
# Role & Permission Matrix
# ============================================================

ROLES = {
    "super_admin": "super_admin",
    "hospital_admin": "hospital_admin",
    "doctor": "doctor",
    "nurse": "nurse",
    "lab_technician": "lab_technician",
    "auditor": "auditor",
}

# The existing system relies on "admin" and "doctor". We will keep them for compatibility
# but map "admin" to "super_admin" semantics, or allow both.

# Matrix: Role -> Set of Permissions (resource:action)
PERMISSION_MATRIX: dict[str, set[str]] = {
    "super_admin": {
        "*",  # Super admin can do anything
    },
    "admin": {
        "*",  # Legacy admin = super admin
    },
    "hospital_admin": {
        "tenant:read",
        "tenant:update",
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
        "audit:read",
    },
    "doctor": {
        "consultation:create",
        "consultation:read",
        "consultation:update",
        "consultation:delete",
        "patient:create",
        "patient:read",
        "patient:update",
        "finding:create",
        "finding:update",
        "finding:read",
        "report:read",
        "report:create",
    },
    "nurse": {
        "patient:create",
        "patient:read",
        "patient:update",
        "consultation:create",
        "consultation:read",
        # Cannot finalize/update diagnoses directly without doctor approval
        "finding:read",
    },
    "lab_technician": {
        "report:create",
        "report:read",
        "patient:read",
    },
    "auditor": {
        "audit:read",
        "consultation:read",
        "patient:read",
        "finding:read",
        "report:read",
        "user:read",
    },
}

# Legacy role hierarchy for backwards compatibility with require_doctor / require_admin
_ROLE_HIERARCHY: dict[str, int] = {
    "auditor": 5,
    "nurse": 8,
    "lab_technician": 8,
    "doctor": 10,
    "hospital_admin": 15,
    "admin": 20,
    "super_admin": 20,
}

_DOCTOR_MIN_LEVEL: int = _ROLE_HIERARCHY["doctor"]
_ADMIN_MIN_LEVEL: int = _ROLE_HIERARCHY["admin"]


# ============================================================
# Core enforcement logic
# ============================================================

def _check_permission(user: User, resource: str, action: str) -> None:  # type: ignore[name-defined]
    """Raise AuthorizationError if the user does not have the required permission."""
    role = getattr(user, "role", None)
    if not role:
        raise AuthorizationError("User has no role assigned.", code="NO_ROLE")
    
    perms = PERMISSION_MATRIX.get(role, set())
    
    if "*" in perms:
        return  # Global override
        
    perm_string = f"{resource}:{action}"
    if perm_string not in perms:
        raise AuthorizationError(
            f"This action requires the '{perm_string}' permission. "
            f"Your account role '{role}' does not grant it.",
            code="INSUFFICIENT_PERMISSIONS",
        )

def _check_role(user: User, min_level: int, role_label: str, error_code: str) -> None:  # type: ignore[name-defined]
    """Legacy role check based on hierarchy."""
    user_level = _ROLE_HIERARCHY.get(getattr(user, "role", ""), 0)
    if user_level < min_level:
        raise AuthorizationError(
            f"This action requires the '{role_label}' role or higher. "
            f"Your account role is '{getattr(user, 'role', 'unknown')}'.",
            code=error_code,
        )


# ============================================================
# Public FastAPI dependency functions
# ============================================================

# Closure factory to generate dependencies for specific permissions
def require_permission(resource: str, action: str) -> Callable:
    """Dependency: require a specific resource and action permission."""
    async def dependency(user: User = Depends(lambda: None)) -> User:  # type: ignore[name-defined]
        _check_permission(user, resource, action)
        return user
    
    # We will wire this dynamically later
    # Attach resource/action to the function for introspection if needed
    dependency._resource = resource  # type: ignore
    dependency._action = action      # type: ignore
    return dependency


async def require_doctor(
    user: User = Depends(lambda: None),
) -> User:  # type: ignore[name-defined]
    """Legacy dependency: require ``doctor`` or ``admin`` role."""
    _check_role(user, _DOCTOR_MIN_LEVEL, "doctor", "REQUIRES_DOCTOR_ROLE")
    return user


async def require_admin(
    user: User = Depends(lambda: None),
) -> User:  # type: ignore[name-defined]
    """Legacy dependency: require ``admin`` role."""
    _check_role(user, _ADMIN_MIN_LEVEL, "admin", "REQUIRES_ADMIN_ROLE")
    return user


# ============================================================
# Wire FastAPI sub-dependencies
# ============================================================

def _wire_dependencies() -> None:
    from app.dependencies import get_current_user, get_db  # noqa: PLC0415
    from sqlalchemy.ext.asyncio import AsyncSession
    
    real_dep = Depends(get_current_user)
    
    require_doctor.__defaults__ = (real_dep,)
    require_admin.__defaults__ = (real_dep,)
    
    global require_permission
    def _wired_require_permission(resource: str, action: str) -> Callable:
        async def dependency(
            user: User = real_dep,
            db: AsyncSession = Depends(get_db),
        ) -> User:  # type: ignore[name-defined]
            _check_permission(user, resource, action)
            
            # Inject tenant scoping for non-admins
            if user.role != "super_admin":
                from sqlalchemy import select
                from app.models.doctor import Doctor
                
                stmt = select(Doctor.tenant_id).where(Doctor.user_id == user.id)
                result = await db.execute(stmt)
                tenant_id = result.scalar_one_or_none()
                
                if tenant_id:
                    db.info["tenant_id"] = tenant_id
            
            return user
        return dependency
    
    require_permission = _wired_require_permission

_wire_dependencies()

async def __lazy_get_db():
    from app.dependencies import get_db
    async for db in get_db():
        yield db

async def get_current_doctor_profile(
    user=Depends(require_doctor),
    db=Depends(__lazy_get_db),
):
    from app.models.doctor import Doctor
    from sqlalchemy import select
    from fastapi import HTTPException, status
    
    stmt = select(Doctor).where(Doctor.user_id == user.id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor profile not found.")
    return doctor
