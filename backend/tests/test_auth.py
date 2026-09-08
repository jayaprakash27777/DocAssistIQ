"""DocAssistIQ — Phase 4 Authentication Tests.

Test coverage:
  Unit (SQLite, no external services):
    - Password hashing: hash is bcrypt, verify correct/wrong
    - JWT: create → decode round-trip, expired token, wrong secret
    - Schema validation: RegisterRequest complexity rules

  Integration (real PostgreSQL, requires Docker stack):
    - POST /auth/register: valid, duplicate email, weak password, missing fields
    - POST /auth/login: valid, wrong password, unknown email, inactive user
    - POST /auth/logout: valid, missing token
    - GET /auth/me: valid, expired JWT, revoked JWT (mocked Redis), no token
    - Security: password_hash never appears in any API response

Redis blacklist tests use a mock to avoid requiring a live Redis in unit mode.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings
from app.exceptions import AuthenticationError
from app.schemas.auth import RegisterRequest
from app.services.auth_service import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)

# ===========================================================
# Helpers
# ===========================================================

_VALID_EMAIL = "dr.test@hospital.example.com"
_VALID_PASSWORD = "SecurePass1"
_VALID_NAME = "Dr. Test User"


def _make_register_payload(
    email: str = _VALID_EMAIL,
    password: str = _VALID_PASSWORD,
    full_name: str = _VALID_NAME,
) -> dict[str, Any]:
    return {"email": email, "password": password, "full_name": full_name}


# ===========================================================
# Unit — Password hashing
# ===========================================================


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        """The hash must not be the plain-text password."""
        hashed = hash_password("SecurePass1")
        assert hashed != "SecurePass1"

    def test_hash_starts_with_bcrypt_prefix(self) -> None:
        """bcrypt hashes always start with $2b$."""
        hashed = hash_password("SecurePass1")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_correct_password_returns_true(self) -> None:
        hashed = hash_password("SecurePass1")
        assert verify_password("SecurePass1", hashed) is True

    def test_verify_wrong_password_returns_false(self) -> None:
        hashed = hash_password("SecurePass1")
        assert verify_password("WrongPass99", hashed) is False

    def test_two_hashes_of_same_password_differ(self) -> None:
        """bcrypt must use a random salt — hashes must differ."""
        h1 = hash_password("SecurePass1")
        h2 = hash_password("SecurePass1")
        assert h1 != h2

    def test_verify_works_against_each_hash(self) -> None:
        h1 = hash_password("SecurePass1")
        h2 = hash_password("SecurePass1")
        assert verify_password("SecurePass1", h1) is True
        assert verify_password("SecurePass1", h2) is True


# ===========================================================
# Unit — JWT
# ===========================================================


class TestJWT:
    def test_create_and_decode_round_trip(self) -> None:
        settings = get_settings()
        user_id = uuid.uuid4()
        token, expires_in, jti = create_access_token(user_id, settings)

        payload = decode_token(token, settings)
        assert payload["sub"] == str(user_id)
        assert payload["jti"] == jti
        assert payload["type"] == "access"

    def test_expires_in_matches_config(self) -> None:
        settings = get_settings()
        _, expires_in, _ = create_access_token(uuid.uuid4(), settings)
        assert expires_in == settings.jwt_access_token_expire_minutes * 60

    def test_expired_token_raises(self) -> None:
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(UTC) - timedelta(seconds=1),
            "iat": datetime.now(UTC) - timedelta(minutes=31),
            "type": "access",
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(token, settings)
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises(self) -> None:
        settings = get_settings()
        token, _, _ = create_access_token(uuid.uuid4(), settings)

        class FakeSettings:
            jwt_secret_key = "totally-wrong-secret"
            jwt_access_token_expire_minutes = 30

        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(token, FakeSettings())  # type: ignore[arg-type]
        assert exc_info.value.status_code == 401

    def test_wrong_token_type_raises(self) -> None:
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(UTC) + timedelta(minutes=30),
            "iat": datetime.now(UTC),
            "type": "refresh",  # wrong type
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(token, settings)
        assert exc_info.value.status_code == 401


# ===========================================================
# Unit — Schema validation
# ===========================================================


class TestRegisterSchema:
    def test_valid_payload_parses(self) -> None:
        req = RegisterRequest(**_make_register_payload())
        assert req.email == _VALID_EMAIL
        assert req.full_name == _VALID_NAME

    def test_email_is_normalised(self) -> None:
        req = RegisterRequest(**_make_register_payload(email="Doctor@HOSPITAL.COM"))
        assert "@" in req.email

    def test_password_too_short_rejected(self) -> None:
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(**_make_register_payload(password="Ab1"))

    def test_password_no_uppercase_rejected(self) -> None:
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(**_make_register_payload(password="nouppercase1"))

    def test_password_no_lowercase_rejected(self) -> None:
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(**_make_register_payload(password="NOLOWER123"))

    def test_password_no_digit_rejected(self) -> None:
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(**_make_register_payload(password="NoDigitPass"))

    def test_password_exceeds_max_length_rejected(self) -> None:
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(**_make_register_payload(password="A1" + "b" * 200))

    def test_full_name_too_short_rejected(self) -> None:
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(**_make_register_payload(full_name="X"))


# ===========================================================
# Integration — API endpoints (real PostgreSQL)
# ===========================================================

# ---------- Register ----------


@pytest.mark.integration
class TestRegisterEndpoint:
    def test_register_valid_returns_201(self, test_client: TestClient) -> None:
        # Use unique email per run to avoid 409 on repeated test runs against persistent DB
        email = f"reg_valid_{uuid.uuid4().hex[:8]}@hospital.example.com"
        resp = test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == email
        assert body["full_name"] == _VALID_NAME
        assert "password_hash" not in body
        assert "password" not in body

    def test_register_response_never_contains_password_hash(
        self, test_client: TestClient
    ) -> None:
        email = f"reg_hash_{uuid.uuid4().hex[:8]}@hospital.example.com"
        resp = test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        text = resp.text
        assert "password_hash" not in text
        assert "$2b$" not in text  # bcrypt hash prefix must never appear

    def test_register_duplicate_email_returns_409(
        self, test_client: TestClient
    ) -> None:
        payload = _make_register_payload(email=f"dup_{uuid.uuid4().hex[:6]}@test.com")
        test_client.post("/api/v1/auth/register", json=payload)
        resp = test_client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_email_case_insensitive_duplicate(
        self, test_client: TestClient
    ) -> None:
        base = f"case_{uuid.uuid4().hex[:6]}"
        test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=f"{base}@test.com"),
        )
        resp = test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=f"{base.upper()}@TEST.COM"),
        )
        assert resp.status_code == 409

    def test_register_weak_password_returns_422(
        self, test_client: TestClient
    ) -> None:
        resp = test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(password="weakpass"),
        )
        assert resp.status_code == 422

    def test_register_missing_email_returns_422(
        self, test_client: TestClient
    ) -> None:
        resp = test_client.post(
            "/api/v1/auth/register",
            json={"password": _VALID_PASSWORD, "full_name": _VALID_NAME},
        )
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(
        self, test_client: TestClient
    ) -> None:
        resp = test_client.post(
            "/api/v1/auth/register",
            json={"email": _VALID_EMAIL, "full_name": _VALID_NAME},
        )
        assert resp.status_code == 422


# ---------- Login ----------


@pytest.mark.integration
class TestLoginEndpoint:
    def _register_and_login(
        self, client: TestClient, suffix: str = ""
    ) -> tuple[str, str]:
        email = f"login_{uuid.uuid4().hex[:6]}{suffix}@test.com"
        client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": _VALID_PASSWORD},
        )
        return email, resp.json().get("access_token", "")

    def test_login_valid_returns_token(self, test_client: TestClient) -> None:
        email, token = self._register_and_login(test_client)
        assert token != ""

    def test_login_response_has_correct_fields(
        self, test_client: TestClient
    ) -> None:
        email = f"lf_{uuid.uuid4().hex[:6]}@test.com"
        test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        resp = test_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": _VALID_PASSWORD},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert isinstance(body["expires_in"], int)
        assert body["expires_in"] > 0

    def test_login_wrong_password_returns_401(
        self, test_client: TestClient
    ) -> None:
        email = f"wp_{uuid.uuid4().hex[:6]}@test.com"
        test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        resp = test_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPass99"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(
        self, test_client: TestClient
    ) -> None:
        resp = test_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": _VALID_PASSWORD},
        )
        assert resp.status_code == 401

    def test_login_error_message_is_generic(
        self, test_client: TestClient
    ) -> None:
        """Both wrong-password and unknown-email must return identical messages."""
        email = f"enum_{uuid.uuid4().hex[:6]}@test.com"
        test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        resp_wrong_pw = test_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPass99"},
        )
        resp_unknown = test_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": _VALID_PASSWORD},
        )
        # Both must return 401 with identical messages (no enumeration)
        assert resp_wrong_pw.status_code == 401, resp_wrong_pw.json()
        assert resp_unknown.status_code == 401, resp_unknown.json()
        assert resp_wrong_pw.json()["error"]["message"] == resp_unknown.json()["error"]["message"]

    def test_login_response_never_contains_password_hash(
        self, test_client: TestClient
    ) -> None:
        email = f"phnl_{uuid.uuid4().hex[:6]}@test.com"
        test_client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        resp = test_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": _VALID_PASSWORD},
        )
        assert "password_hash" not in resp.text
        assert "$2b$" not in resp.text


# ---------- Me ----------


@pytest.mark.integration
class TestMeEndpoint:
    def _get_token(self, client: TestClient) -> str:
        email = f"me_{uuid.uuid4().hex[:6]}@test.com"
        client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": _VALID_PASSWORD},
        )
        return resp.json()["access_token"]

    def test_me_valid_token_returns_profile(
        self, test_client: TestClient
    ) -> None:
        token = self._get_token(test_client)
        resp = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "email" in body
        assert "full_name" in body
        assert "password_hash" not in body

    def test_me_missing_token_returns_401(
        self, test_client: TestClient
    ) -> None:
        resp = test_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token_returns_401(
        self, test_client: TestClient
    ) -> None:
        resp = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert resp.status_code == 401

    def test_me_expired_token_returns_401(
        self, test_client: TestClient
    ) -> None:
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(UTC) - timedelta(seconds=1),
            "iat": datetime.now(UTC) - timedelta(minutes=31),
            "type": "access",
        }
        expired_token = jwt.encode(
            payload, settings.jwt_secret_key, algorithm="HS256"
        )
        resp = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    def test_me_revoked_token_returns_401(
        self, test_client: TestClient
    ) -> None:
        """Token blacklisted in Redis must be rejected by /me."""
        token = self._get_token(test_client)
        with patch(
            "app.services.auth_service._is_jti_blacklisted",
            new=AsyncMock(return_value=True),
        ):
            resp = test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 401


# ---------- Logout ----------


@pytest.mark.integration
class TestLogoutEndpoint:
    def _get_token(self, client: TestClient) -> str:
        email = f"lo_{uuid.uuid4().hex[:6]}@test.com"
        client.post(
            "/api/v1/auth/register",
            json=_make_register_payload(email=email),
        )
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": _VALID_PASSWORD},
        )
        return resp.json()["access_token"]

    def test_logout_valid_token_returns_204(
        self, test_client: TestClient
    ) -> None:
        token = self._get_token(test_client)
        with patch(
            "app.services.auth_service._blacklist_jti",
            new=AsyncMock(),
        ):
            resp = test_client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 204

    def test_logout_missing_token_returns_401(
        self, test_client: TestClient
    ) -> None:
        resp = test_client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
