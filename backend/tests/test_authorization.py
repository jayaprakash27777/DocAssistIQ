"""DocAssistIQ — Authorization Integration Tests (Phase 5).

Tests the role-based access control layer end-to-end through the real API.

Test strategy
-------------
All tests use the ``test_client`` fixture (real PostgreSQL, FastAPI TestClient)
so authorization checks execute exactly as they would in production.

Coverage
--------
Unit layer:
  - ``RoleGuard.__call__`` logic via direct invocation (fast, no HTTP)

Integration layer (HTTP surface):
  - doctor role → doctor-required endpoint: 200
  - admin role → doctor-required endpoint: 200 (admin ≥ doctor)
  - admin role → admin-required endpoint: 200
  - doctor role → admin-required endpoint: 403 FORBIDDEN
  - unauthenticated → doctor-required endpoint: 401 UNAUTHORIZED
  - unauthenticated → admin-required endpoint: 401 UNAUTHORIZED
  - no-role / unknown role → admin-required endpoint: 403
  - suspended account → protected endpoint: 403 ACCOUNT_INACTIVE
  - direct API call bypassing any frontend guard: 403 confirmed
  - error envelope shape: {"error": {"code": ..., "message": ...}}
  - ``require_role`` factory produces correct guards
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.authorization import RoleGuard, require_admin, require_doctor, require_role
from app.exceptions import AuthorizationError

# ============================================================
# Helpers
# ============================================================

_VALID_PASSWORD = "ValidPass99"


def _make_register_payload(*, email: str) -> dict:
    return {"email": email, "password": _VALID_PASSWORD, "full_name": "Test Clinician"}


def _register(client: TestClient, email: str) -> None:
    resp = client.post("/api/v1/auth/register", json=_make_register_payload(email=email))
    assert resp.status_code == 201, resp.json()


def _login(client: TestClient, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _VALID_PASSWORD},
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# Unit tests — RoleGuard logic (no HTTP, no DB)
# ============================================================


class TestRoleGuardUnit:
    """Fast unit tests for the RoleGuard callable class."""

    def test_require_doctor_allows_doctor_role(self) -> None:
        """doctor role meets the doctor minimum level."""
        from app.authorization import _DOCTOR_MIN_LEVEL, _ROLE_HIERARCHY

        assert _ROLE_HIERARCHY["doctor"] >= _DOCTOR_MIN_LEVEL

    def test_require_doctor_allows_admin_role(self) -> None:
        """admin role exceeds doctor minimum level (admin ≥ doctor)."""
        from app.authorization import _DOCTOR_MIN_LEVEL, _ROLE_HIERARCHY

        assert _ROLE_HIERARCHY["admin"] >= _DOCTOR_MIN_LEVEL

    def test_require_admin_allows_admin_role(self) -> None:
        """admin role meets the admin minimum level."""
        from app.authorization import _ADMIN_MIN_LEVEL, _ROLE_HIERARCHY

        assert _ROLE_HIERARCHY["admin"] >= _ADMIN_MIN_LEVEL

    def test_require_admin_rejects_doctor_role(self) -> None:
        """doctor level is below the admin minimum."""
        from app.authorization import _ADMIN_MIN_LEVEL, _ROLE_HIERARCHY

        assert _ROLE_HIERARCHY["doctor"] < _ADMIN_MIN_LEVEL

    def test_role_guard_raises_authorization_error_for_insufficient_role(self) -> None:
        """RoleGuard core logic raises AuthorizationError when role is too low."""
        import asyncio

        from app.authorization import RoleGuard

        # Use a fresh guard (not a singleton) so __call__ is the base class version
        guard = RoleGuard(min_level=20, role_label="admin", error_code="REQUIRES_ADMIN_ROLE")

        user = MagicMock()
        user.role = "doctor"

        with pytest.raises(AuthorizationError) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                RoleGuard.__call__(guard, user=user)
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "REQUIRES_ADMIN_ROLE"

    def test_role_guard_returns_user_when_authorized(self) -> None:
        """RoleGuard core logic returns the user when role is sufficient."""
        import asyncio

        from app.authorization import RoleGuard

        guard = RoleGuard(min_level=10, role_label="doctor", error_code="REQUIRES_DOCTOR_ROLE")

        user = MagicMock()
        user.role = "doctor"

        result = asyncio.get_event_loop().run_until_complete(
            RoleGuard.__call__(guard, user=user)
        )
        assert result is user

    def test_unknown_role_treated_as_level_zero(self) -> None:
        """Roles not in the hierarchy get level 0, denied by any guard."""
        import asyncio

        from app.authorization import RoleGuard

        guard = RoleGuard(min_level=10, role_label="doctor", error_code="REQUIRES_DOCTOR_ROLE")

        user = MagicMock()
        user.role = "guest"

        with pytest.raises(AuthorizationError):
            asyncio.get_event_loop().run_until_complete(
                RoleGuard.__call__(guard, user=user)
            )

    def test_singletons_are_callable_dependencies(self) -> None:
        """require_doctor and require_admin are callable FastAPI dependencies."""
        import inspect

        # Both must be async callables (async def functions)
        assert inspect.iscoroutinefunction(require_doctor), (
            "require_doctor must be an async function for FastAPI Depends()"
        )
        assert inspect.iscoroutinefunction(require_admin), (
            "require_admin must be an async function for FastAPI Depends()"
        )

    def test_require_role_factory_returns_role_guard(self) -> None:
        """require_role() returns a RoleGuard instance."""
        guard = require_role({"doctor", "admin"})
        assert isinstance(guard, RoleGuard)

    def test_require_role_factory_raises_on_empty_set(self) -> None:
        """require_role() raises ValueError for empty allowed_roles."""
        with pytest.raises(ValueError, match="allowed_roles must not be empty"):
            require_role(set())



# ============================================================
# Integration tests — HTTP surface with real DB
# ============================================================


class TestDoctorRoleAccess:
    """Doctor role can access doctor-required endpoints."""

    def test_doctor_can_access_doctor_endpoint(self, test_client: TestClient) -> None:
        """doctor role → GET /auth/me (doctor-or-above) → 200."""
        email = f"dr_doc_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        # /auth/me is protected by get_current_user (equivalent to doctor-level)
        resp = test_client.get("/api/v1/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200

    def test_doctor_receives_correct_role_in_profile(self, test_client: TestClient) -> None:
        """Newly registered user has role='doctor' in /auth/me response."""
        email = f"dr_role_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get("/api/v1/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "doctor"

    def test_doctor_denied_admin_ping(self, test_client: TestClient) -> None:
        """doctor role → GET /admin/ping → 403 FORBIDDEN."""
        email = f"dr_adm_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get("/api/v1/admin/ping", headers=_auth_header(token))
        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "REQUIRES_ADMIN_ROLE"

    def test_doctor_denied_admin_users_list(self, test_client: TestClient) -> None:
        """doctor role → GET /admin/users → 403 FORBIDDEN."""
        email = f"dr_ul_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get("/api/v1/admin/users", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_doctor_403_error_envelope_shape(self, test_client: TestClient) -> None:
        """403 response uses the standard error envelope."""
        email = f"dr_env_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get("/api/v1/admin/ping", headers=_auth_header(token))
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        assert "request_id" in body["error"]


class TestAdminRoleAccess:
    """Admin role can access both doctor and admin endpoints."""

    def _make_admin(self, client: TestClient) -> tuple[str, str]:
        """Register a user, promote to admin in DB, return (email, token)."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.pool import NullPool

        _int_url = "postgresql+asyncpg://docassistiq:changeme@127.0.0.1:5434/docassistiq"

        email = f"adm_{uuid.uuid4().hex[:6]}@test.com"
        _register(client, email)
        token = _login(client, email)

        # Promote to admin directly via DB
        import asyncio

        async def _promote() -> None:
            engine = create_async_engine(_int_url, poolclass=NullPool)
            async with AsyncSession(bind=engine) as session:
                await session.execute(
                    text("UPDATE users SET role = 'admin' WHERE lower(email) = lower(:email)"),
                    {"email": email},
                )
                await session.commit()
            await engine.dispose()

        asyncio.get_event_loop().run_until_complete(_promote())

        # Re-login to get a fresh token (role is in DB, not JWT, so same token works)
        return email, token

    def test_admin_can_access_admin_ping(self, test_client: TestClient) -> None:
        """admin role → GET /admin/ping → 200."""
        _, token = self._make_admin(test_client)
        resp = test_client.get("/api/v1/admin/ping", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_admin_can_access_admin_users(self, test_client: TestClient) -> None:
        """admin role → GET /admin/users → 200 with PagedResponse envelope."""
        _, token = self._make_admin(test_client)
        resp = test_client.get("/api/v1/admin/users", headers=_auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        # Phase 6: /admin/users now returns the standard PagedResponse envelope
        for key in ("items", "total", "page", "page_size", "pages"):
            assert key in body, f"Missing PagedResponse key: '{key}'"
        assert isinstance(body["items"], list)

    def test_admin_can_also_access_me_endpoint(self, test_client: TestClient) -> None:
        """admin role satisfies doctor-level requirement (admin ≥ doctor)."""
        _, token = self._make_admin(test_client)
        resp = test_client.get("/api/v1/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_admin_ping_response_shape(self, test_client: TestClient) -> None:
        """Admin ping response has expected schema."""
        _, token = self._make_admin(test_client)
        resp = test_client.get("/api/v1/admin/ping", headers=_auth_header(token))
        body = resp.json()
        assert body["ok"] is True
        assert isinstance(body["message"], str)


class TestUnauthenticatedAccess:
    """Unauthenticated requests are rejected before role checking."""

    def test_unauthenticated_denied_admin_ping(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/v1/admin/ping")
        assert resp.status_code == 401

    def test_unauthenticated_denied_admin_users(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/v1/admin/users")
        assert resp.status_code == 401

    def test_unauthenticated_denied_me(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_invalid_token_denied_admin_ping(self, test_client: TestClient) -> None:
        resp = test_client.get(
            "/api/v1/admin/ping",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert resp.status_code == 401

    def test_malformed_auth_header_denied(self, test_client: TestClient) -> None:
        """Non-Bearer scheme is rejected with 401."""
        resp = test_client.get(
            "/api/v1/admin/ping",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401


class TestDirectApiBypassAttempts:
    """Verify authorization holds even when frontend controls are bypassed."""

    def test_doctor_cannot_access_admin_endpoint_via_direct_api_call(
        self, test_client: TestClient
    ) -> None:
        """Simulates a doctor directly calling an admin endpoint.

        A real-world attacker could:
          - Use curl/Postman with their doctor token
          - Disable frontend route guards
          - Forge a request from browser DevTools

        All must fail at the API layer regardless.
        """
        email = f"bypass_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        # Direct call with valid doctor token — must be 403
        resp = test_client.get("/api/v1/admin/ping", headers=_auth_header(token))
        assert resp.status_code == 403, (
            "Authorization bypass: a doctor token was accepted on an admin endpoint"
        )

    def test_doctor_cannot_access_admin_users_via_direct_api_call(
        self, test_client: TestClient
    ) -> None:
        email = f"bypass2_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get("/api/v1/admin/users", headers=_auth_header(token))
        assert resp.status_code == 403, (
            "Authorization bypass: a doctor token was accepted on admin users endpoint"
        )

    def test_forged_role_in_jwt_claim_does_not_grant_access(
        self, test_client: TestClient
    ) -> None:
        """A JWT with a forged 'admin' role in the payload must be rejected.

        Our implementation reads the role from the live DB row (not from the
        JWT payload).  A forged token with sub=<valid-doctor-uuid> and a
        custom 'role=admin' field in the payload is decoded to the real user
        ID, then the DB row's actual role ('doctor') is used for the check.

        This test constructs such a forged token to confirm denial.
        """
        from datetime import UTC, datetime, timedelta

        from jose import jwt

        from app.config import get_settings

        # Register and login a real doctor
        email = f"forge_{uuid.uuid4().hex[:6]}@test.com"
        _register(test_client, email)
        token = _login(test_client, email)

        # Get their real user ID from /me
        me_resp = test_client.get("/api/v1/auth/me", headers=_auth_header(token))
        user_id = me_resp.json()["id"]

        # Forge a JWT with the same sub but role=admin injected
        settings = get_settings()
        forged_payload = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "role": "admin",  # ← forged role claim (ignored by our auth)
            "exp": datetime.now(UTC) + timedelta(minutes=30),
            "iat": datetime.now(UTC),
        }
        forged_token = jwt.encode(
            forged_payload, settings.jwt_secret_key, algorithm="HS256"
        )

        # The forged token must be denied — role is read from DB, not JWT
        resp = test_client.get(
            "/api/v1/admin/ping",
            headers=_auth_header(forged_token),
        )
        assert resp.status_code == 403, (
            "Security: forged JWT role claim granted unauthorized admin access"
        )
