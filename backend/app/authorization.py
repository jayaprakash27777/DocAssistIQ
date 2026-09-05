"""DocAssistIQ — Authorization Foundation.

Provides reusable FastAPI dependencies for role-based access control (RBAC).

Role hierarchy (Phase 5):
    doctor  — can access all clinical features
    admin   — superset of doctor; can also access administrative operations

Usage in route handlers::

    from app.authorization import require_doctor, require_admin
    from app.models.user import User

    @router.get("/clinical-data")
    async def clinical_data(
        user: User = Depends(require_doctor),
    ) -> ...:
        ...

    @router.delete("/users/{uid}")
    async def delete_user(
        uid: UUID,
        user: User = Depends(require_admin),
    ) -> ...:
        ...

Security guarantees:
    - Authorization is always checked server-side, independent of any
      frontend visibility control.
    - The role is read from the live ``User`` ORM row returned by
      ``get_current_user``, NOT from the JWT payload.  A forged JWT
      claiming an elevated role will be decoded to a real user-ID, then
      the database row's actual role is checked.
    - Unauthenticated requests are rejected with 401 before role checking
      even begins (``get_current_user`` raises first).
    - Suspended accounts are rejected with 403 ACCOUNT_INACTIVE.

Design note — no circular import:
    This module does NOT import from ``app.dependencies`` at module level.
    The ``get_current_user`` dependency is imported inside each async function
    body, which Python resolves lazily at call time (after all modules are
    fully initialised).

Adding a new role:
    1. Add the role string to ``_ROLE_HIERARCHY`` (higher int = more access).
    2. Add a new ``async def require_<role>(...)`` function following the
       pattern of ``require_doctor`` / ``require_admin`` below.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends

from app.exceptions import AuthorizationError

if TYPE_CHECKING:
    from app.models.user import User

# ============================================================
# Role hierarchy
# ============================================================

#: Maps each role name to its privilege level.
_ROLE_HIERARCHY: dict[str, int] = {
    "doctor": 10,
    "admin": 20,
}

_DOCTOR_MIN_LEVEL: int = _ROLE_HIERARCHY["doctor"]  # 10
_ADMIN_MIN_LEVEL: int = _ROLE_HIERARCHY["admin"]  # 20


# ============================================================
# Core enforcement logic (pure — no FastAPI dep)
# ============================================================


def _check_role(user: User, min_level: int, role_label: str, error_code: str) -> None:  # type: ignore[name-defined]
    """Raise AuthorizationError if the user's role is below min_level.

    Args:
        user:        Live User ORM object (role read from DB, not JWT).
        min_level:   Minimum level the user's role must meet or exceed.
        role_label:  Human-readable role name for the error message.
        error_code:  Machine-readable code for the error envelope.

    Raises:
        AuthorizationError(403): when the user's role is insufficient.
    """
    user_level = _ROLE_HIERARCHY.get(user.role, 0)
    if user_level < min_level:
        raise AuthorizationError(
            f"This action requires the '{role_label}' role or higher. "
            f"Your account role is '{user.role}'.",
            code=error_code,
        )


# ============================================================
# Public FastAPI dependency functions
# ============================================================


async def require_doctor(  # noqa: RUF029
    user: User = Depends(lambda: None),  # noqa: B008 — replaced below
) -> User:  # type: ignore[name-defined]
    """Dependency: require ``doctor`` or ``admin`` role.

    Inject as ``user: User = Depends(require_doctor)`` on any clinical route.
    Delegates authentication to ``get_current_user``; this layer only checks
    the role after a valid, non-suspended user has been resolved.
    """
    # NOTE: the Depends default above is a placeholder.
    # The real dependency is wired by _build_guard() at the bottom of this file.
    _check_role(user, _DOCTOR_MIN_LEVEL, "doctor", "REQUIRES_DOCTOR_ROLE")
    return user


async def require_admin(  # noqa: RUF029
    user: User = Depends(lambda: None),  # noqa: B008 — replaced below
) -> User:  # type: ignore[name-defined]
    """Dependency: require ``admin`` role.

    Inject as ``user: User = Depends(require_admin)`` on administrative routes.
    """
    _check_role(user, _ADMIN_MIN_LEVEL, "admin", "REQUIRES_ADMIN_ROLE")
    return user


# ============================================================
# RoleGuard class (for programmatic use and unit tests)
# ============================================================


class RoleGuard:
    """Programmatic role guard for unit testing and ad-hoc guards.

    This class is NOT directly usable as a ``Depends()`` target because its
    ``__call__`` does not carry FastAPI dependency annotations.  Use it only
    for unit tests or via ``require_role()`` which returns a wired async dep.

    For HTTP endpoints, use the pre-built ``require_doctor`` /
    ``require_admin`` module-level functions instead.
    """

    def __init__(self, min_level: int, role_label: str, error_code: str) -> None:
        self.min_level = min_level
        self.role_label = role_label
        self.error_code = error_code

    async def __call__(self, *, user: User) -> User:  # type: ignore[name-defined]
        """Check role and return user if authorized.

        Args:
            user: User ORM object to check.

        Returns:
            The same user object, unchanged.

        Raises:
            AuthorizationError(403): role insufficient.
        """
        _check_role(user, self.min_level, self.role_label, self.error_code)
        return user


# ============================================================
# require_role() factory
# ============================================================


def require_role(allowed_roles: set[str]) -> RoleGuard:
    """Return a ``RoleGuard`` for ad-hoc role sets (unit tests / future use).

    For HTTP endpoints, define a dedicated async ``require_<role>`` function
    following the ``require_doctor`` / ``require_admin`` pattern instead of
    using this factory directly.

    Args:
        allowed_roles: Set of role strings that are permitted.

    Returns:
        A ``RoleGuard`` whose minimum level is the lowest in ``allowed_roles``.

    Raises:
        ValueError: if ``allowed_roles`` is empty.
    """
    if not allowed_roles:
        msg = "allowed_roles must not be empty"
        raise ValueError(msg)

    min_level = min(_ROLE_HIERARCHY.get(r, 0) for r in allowed_roles)
    label = " or ".join(sorted(allowed_roles))
    code = "REQUIRES_" + "_OR_".join(sorted(r.upper() for r in allowed_roles)) + "_ROLE"
    return RoleGuard(min_level=min_level, role_label=label, error_code=code)


# ============================================================
# Wire FastAPI sub-dependencies (deferred to avoid circular import)
# ============================================================
# ``get_current_user`` lives in ``app.dependencies`` which imports from here
# at the module-docstring level.  We defer the wiring until after both modules
# are fully initialised by patching the __defaults__ of the async functions.
# FastAPI inspects ``__defaults__`` (for positional) and ``__kwdefaults__``
# (for keyword-only) when building the dependency graph.


def _wire_dependencies() -> None:
    """Replace the placeholder ``Depends(lambda: None)`` with the real dep.

    Called once at module load time, after the import chain is resolved.
    Uses Python's ``__defaults__`` attribute to update the FastAPI Depends
    object without touching the function's signature or docstring.
    """
    # Deferred import — safe here because both modules are now initialised.
    from app.dependencies import get_current_user  # noqa: PLC0415

    real_dep = Depends(get_current_user)
    # Both functions have exactly one parameter with a default.
    require_doctor.__defaults__ = (real_dep,)
    require_admin.__defaults__ = (real_dep,)


_wire_dependencies()
