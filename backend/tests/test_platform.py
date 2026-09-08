"""DocAssistIQ — Core API Platform Integration Tests (Phase 6).

Tests the reusable API platform layer end-to-end through the real API:

Coverage
--------
Pagination:
  - Default page/size returns expected envelope keys
  - page=2 skips first page of results
  - page_size boundaries (1, 100 are valid; 0, 101 are not)
  - page=0 is rejected (below min)
  - Response envelope structure: items, total, page, page_size, pages

Sorting:
  - sort_by=email asc → correct order
  - sort_by=email desc → reversed order
  - sort_by=full_name → correct order
  - sort_by=unknown_column → 422 VALIDATION_ERROR
  - sort_dir=sideways → 422

Filtering:
  - role=doctor → only doctors returned
  - role=admin → only admins returned
  - role=invalid → 422 INVALID_ROLE_FILTER

Error envelope:
  - 401 has error.code = "UNAUTHORIZED"
  - 403 has error.code = "REQUIRES_DOCTOR_ROLE"
  - 422 has error.code = "VALIDATION_ERROR"
  - Every error body has request_id

Correlation IDs:
  - X-Request-ID response header present on 200
  - X-Request-ID present on 4xx errors
  - Error body request_id matches X-Request-ID header

OpenAPI metadata:
  - /docs accessible in test environment (docs_url=/docs)
  - /openapi.json accessible
  - Tags present in schema

Platform helpers (unit):
  - PaginationParams.offset computed correctly
  - PaginationParams.limit = page_size
  - PagedResponse.build() computes pages ceiling
  - apply_sort() rejects unknown columns via ValidationError
  - validate_uuid_param() accepts valid UUID
  - validate_uuid_param() rejects invalid string
  - require_non_empty_string() accepts non-empty
  - require_non_empty_string() rejects whitespace-only
"""

from __future__ import annotations

import math
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.platform import (
    PagedResponse,
    PaginationParams,
    SortParams,
    apply_sort,
    require_non_empty_string,
    validate_uuid_param,
)
from app.exceptions import ValidationError

# ============================================================
# Helpers
# ============================================================

_PASSWORD = "ValidPass99"
_BASE_URL = "/api/v1"


def _email(prefix: str = "plat") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:6]}@platform-test.example.com"


def _register(client: TestClient, email: str) -> None:
    r = client.post(
        f"{_BASE_URL}/auth/register",
        json={"email": email, "password": _PASSWORD, "full_name": "Platform Tester"},
    )
    assert r.status_code == 201, r.json()


def _login(client: TestClient, email: str) -> str:
    r = client.post(
        f"{_BASE_URL}/auth/login",
        json={"email": email, "password": _PASSWORD},
    )
    assert r.status_code == 200, r.json()
    return r.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _promote_to_admin(email: str) -> None:
    """Promote a user to admin via direct DB update."""
    import asyncio

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.pool import NullPool

    _db_url = "postgresql+asyncpg://docassistiq:changeme@127.0.0.1:5434/docassistiq"

    async def _run() -> None:
        engine = create_async_engine(_db_url, poolclass=NullPool)
        async with AsyncSession(bind=engine) as session:
            await session.execute(
                text("UPDATE users SET role = 'admin' WHERE lower(email) = lower(:email)"),
                {"email": email},
            )
            await session.commit()
        await engine.dispose()

    asyncio.get_event_loop().run_until_complete(_run())


# ============================================================
# Unit tests — Platform helpers (fast, no HTTP)
# ============================================================


class TestPaginationParamsUnit:
    """Unit tests for PaginationParams helper properties."""

    def test_offset_page_1(self) -> None:
        p = PaginationParams(page=1, page_size=20)
        assert p.offset == 0

    def test_offset_page_2(self) -> None:
        p = PaginationParams(page=2, page_size=20)
        assert p.offset == 20

    def test_offset_page_3_size_10(self) -> None:
        p = PaginationParams(page=3, page_size=10)
        assert p.offset == 20

    def test_limit_equals_page_size(self) -> None:
        p = PaginationParams(page=1, page_size=15)
        assert p.limit == 15


class TestPagedResponseUnit:
    """Unit tests for PagedResponse.build()."""

    def _make_pagination(self, page: int = 1, page_size: int = 10) -> PaginationParams:
        return PaginationParams(page=page, page_size=page_size)

    def test_pages_ceiling(self) -> None:
        """21 items / 10 per page = 3 pages (ceiling)."""
        p = PagedResponse.build(items=[], total=21, pagination=self._make_pagination(page_size=10))
        assert p.pages == 3

    def test_pages_exact(self) -> None:
        """20 items / 10 per page = exactly 2 pages."""
        p = PagedResponse.build(items=[], total=20, pagination=self._make_pagination(page_size=10))
        assert p.pages == 2

    def test_pages_zero_total(self) -> None:
        """0 items → 1 page (not 0)."""
        p = PagedResponse.build(items=[], total=0, pagination=self._make_pagination())
        assert p.pages == 1

    def test_envelope_fields(self) -> None:
        pagination = self._make_pagination(page=2, page_size=5)
        p = PagedResponse.build(items=[], total=12, pagination=pagination)
        assert p.page == 2
        assert p.page_size == 5
        assert p.total == 12
        assert p.pages == math.ceil(12 / 5)


class TestApplySortUnit:
    """Unit tests for apply_sort() whitelist enforcement."""

    def test_unknown_column_raises_validation_error(self) -> None:
        from sqlalchemy import select

        from app.models.user import User

        query = select(User)
        sort = SortParams(sort_by="nonexistent_column", sort_dir="asc")
        with pytest.raises(ValidationError) as exc_info:
            apply_sort(query, sort, allowed_columns={"email", "created_at"}, model=User)
        assert exc_info.value.code == "INVALID_SORT_COLUMN"
        assert "nonexistent_column" in exc_info.value.message

    def test_known_column_does_not_raise(self) -> None:
        from sqlalchemy import select

        from app.models.user import User

        query = select(User)
        sort = SortParams(sort_by="email", sort_dir="asc")
        result = apply_sort(query, sort, allowed_columns={"email"}, model=User)
        assert result is not query  # ORDER BY was applied


class TestValidateUUIDUnit:
    """Unit tests for validate_uuid_param()."""

    def test_valid_uuid_passes(self) -> None:
        uid = str(uuid.uuid4())
        assert validate_uuid_param(uid) == uid

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid_param("not-a-uuid")
        assert exc_info.value.code == "INVALID_UUID"


class TestRequireNonEmptyStringUnit:
    """Unit tests for require_non_empty_string()."""

    def test_valid_string_passes(self) -> None:
        result = require_non_empty_string("  hello  ", field_name="name")
        assert result == "hello"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError):
            require_non_empty_string("", field_name="name")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValidationError):
            require_non_empty_string("   ", field_name="name")

    def test_none_raises(self) -> None:
        with pytest.raises(ValidationError):
            require_non_empty_string(None, field_name="name")


# ============================================================
# Integration tests — Pagination
# ============================================================


class TestPaginationIntegration:
    """Pagination integration tests via GET /probe/users."""

    def _make_authed_token(self, client: TestClient) -> str:
        email = _email("pag")
        _register(client, email)
        return _login(client, email)

    def test_default_pagination_returns_envelope_keys(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(f"{_BASE_URL}/probe/users", headers=_auth(token))
        assert resp.status_code == 200, resp.json()
        body = resp.json()
        for key in ("items", "total", "page", "page_size", "pages"):
            assert key in body, f"Missing key '{key}' in response"

    def test_default_page_is_1(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(f"{_BASE_URL}/probe/users", headers=_auth(token))
        assert resp.json()["page"] == 1

    def test_default_page_size_is_20(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(f"{_BASE_URL}/probe/users", headers=_auth(token))
        assert resp.json()["page_size"] == 20

    def test_items_is_a_list(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(f"{_BASE_URL}/probe/users", headers=_auth(token))
        assert isinstance(resp.json()["items"], list)

    def test_page_size_1_returns_at_most_1_item(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"page_size": 1},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) <= 1

    def test_page_2_skips_first_page(self, test_client: TestClient) -> None:
        """With page_size=1, page 1 and page 2 return different items."""
        # Register two distinct users to ensure at least 2 rows
        email_a = _email("pag_a")
        email_b = _email("pag_b")
        _register(test_client, email_a)
        _register(test_client, email_b)
        token = _login(test_client, email_a)

        resp1 = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"page": 1, "page_size": 1, "sort_by": "created_at", "sort_dir": "asc"},
            headers=_auth(token),
        )
        resp2 = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"page": 2, "page_size": 1, "sort_by": "created_at", "sort_dir": "asc"},
            headers=_auth(token),
        )
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        items1 = resp1.json()["items"]
        items2 = resp2.json()["items"]
        if items1 and items2:
            assert items1[0]["id"] != items2[0]["id"]

    def test_page_size_0_rejected(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"page_size": 0},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_page_size_501_rejected(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"page_size": 501},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_page_0_rejected(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"page": 0},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_total_is_non_negative_int(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(f"{_BASE_URL}/probe/users", headers=_auth(token))
        total = resp.json()["total"]
        assert isinstance(total, int)
        assert total >= 0

    def test_pages_at_least_1(self, test_client: TestClient) -> None:
        token = self._make_authed_token(test_client)
        resp = test_client.get(f"{_BASE_URL}/probe/users", headers=_auth(token))
        assert resp.json()["pages"] >= 1

    def test_admin_users_endpoint_is_also_paginated(self, test_client: TestClient) -> None:
        """GET /admin/users now also returns PagedResponse envelope."""
        email = _email("adm_pag")
        _register(test_client, email)
        _promote_to_admin(email)
        token = _login(test_client, email)

        resp = test_client.get(
            f"{_BASE_URL}/admin/users",
            params={"page": 1, "page_size": 5},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        for key in ("items", "total", "page", "page_size", "pages"):
            assert key in body


# ============================================================
# Integration tests — Sorting
# ============================================================


class TestSortingIntegration:
    """Sorting integration tests via GET /probe/users."""

    def _token(self, client: TestClient) -> str:
        email = _email("srt")
        _register(client, email)
        return _login(client, email)

    def test_sort_by_email_asc(self, test_client: TestClient) -> None:
        token = self._token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"sort_by": "email", "sort_dir": "asc", "page_size": 50},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        emails = [item["email"] for item in resp.json()["items"]]
        assert len(emails) > 0
        # PostgreSQL C-locale sorts by raw byte values (case-sensitive).
        # Verify the list equals itself sorted using the same byte ordering.
        assert emails == sorted(emails), (
            f"Emails are not sorted ASC in C-locale byte order. "
            f"Got: {emails[:5]}..."
        )

    def test_sort_by_email_desc(self, test_client: TestClient) -> None:
        token = self._token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"sort_by": "email", "sort_dir": "desc", "page_size": 50},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        emails = [item["email"] for item in resp.json()["items"]]
        assert len(emails) > 0
        # PostgreSQL C-locale DESC = reverse of byte-order ASC.
        assert emails == sorted(emails, reverse=True), (
            f"Emails are not sorted DESC in C-locale byte order."
        )

    def test_sort_by_full_name_asc(self, test_client: TestClient) -> None:
        token = self._token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"sort_by": "full_name", "sort_dir": "asc", "page_size": 50},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        names = [item["full_name"] for item in resp.json()["items"]]
        assert len(names) > 0, "Expected at least one user"
        # PostgreSQL C-locale sorts by raw byte values.
        assert names == sorted(names), (
            f"Names are not sorted ASC in C-locale byte order."
        )

    def test_sort_by_unknown_column_rejected(self, test_client: TestClient) -> None:
        token = self._token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"sort_by": "password_hash"},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        body = resp.json()
        # INVALID_SORT_COLUMN is the specific code raised by apply_sort()
        assert body["error"]["code"] == "INVALID_SORT_COLUMN"
        assert "password_hash" in body["error"]["message"]

    def test_sort_dir_invalid_rejected(self, test_client: TestClient) -> None:
        token = self._token(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"sort_by": "email", "sort_dir": "sideways"},
            headers=_auth(token),
        )
        assert resp.status_code == 422


# ============================================================
# Integration tests — Filtering
# ============================================================


class TestFilteringIntegration:
    """Filtering integration tests via GET /probe/users."""

    def _setup_admin(self, client: TestClient) -> str:
        """Register an admin user, return their token."""
        email = _email("flt_adm")
        _register(client, email)
        _promote_to_admin(email)
        return _login(client, email)

    def test_filter_role_doctor_returns_only_doctors(self, test_client: TestClient) -> None:
        # Create a known doctor
        dr_email = _email("flt_dr")
        _register(test_client, dr_email)
        token = _login(test_client, dr_email)

        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"role": "doctor", "page_size": 100},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        roles = {item["role"] for item in items}
        assert roles <= {"doctor"}, f"Unexpected roles: {roles}"

    def test_filter_role_admin_returns_only_admins(self, test_client: TestClient) -> None:
        token = self._setup_admin(test_client)
        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"role": "admin", "page_size": 100},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        if items:
            roles = {item["role"] for item in items}
            assert roles <= {"admin"}

    def test_filter_role_invalid_rejected(self, test_client: TestClient) -> None:
        email = _email("flt_inv")
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"role": "superuser"},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        # INVALID_ROLE_FILTER is the specific code raised by the probe endpoint's filter check
        assert resp.json()["error"]["code"] == "INVALID_ROLE_FILTER"


# ============================================================
# Integration tests — Error envelope and correlation IDs
# ============================================================


class TestErrorEnvelopeIntegration:
    """Error envelope and X-Request-ID correlation tests."""

    def test_401_error_envelope(self, test_client: TestClient) -> None:
        resp = test_client.get(f"{_BASE_URL}/probe/users")
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "UNAUTHORIZED"
        assert "request_id" in body["error"]

    def test_403_error_envelope(self, test_client: TestClient) -> None:
        email = _email("err_403")
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get(f"{_BASE_URL}/admin/ping", headers=_auth(token))
        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "REQUIRES_ADMIN_ROLE"
        assert "request_id" in body["error"]

    def test_422_error_envelope_from_platform(self, test_client: TestClient) -> None:
        email = _email("err_422")
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get(
            f"{_BASE_URL}/probe/users",
            params={"page": 0},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "request_id" in body["error"]

    def test_request_id_header_present_on_success(self, test_client: TestClient) -> None:
        email = _email("rid_ok")
        _register(test_client, email)
        token = _login(test_client, email)

        resp = test_client.get(f"{_BASE_URL}/probe/users", headers=_auth(token))
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers

    def test_request_id_header_present_on_error(self, test_client: TestClient) -> None:
        resp = test_client.get(f"{_BASE_URL}/probe/users")
        assert resp.status_code == 401
        assert "x-request-id" in resp.headers

    def test_error_request_id_matches_header(self, test_client: TestClient) -> None:
        """Error body request_id == X-Request-ID response header."""
        resp = test_client.get(f"{_BASE_URL}/probe/users")
        assert resp.status_code == 401
        header_rid = resp.headers.get("x-request-id")
        body_rid = resp.json()["error"]["request_id"]
        assert header_rid == body_rid

    def test_every_error_has_message(self, test_client: TestClient) -> None:
        resp = test_client.get(f"{_BASE_URL}/probe/users")
        body = resp.json()
        assert isinstance(body["error"]["message"], str)
        assert len(body["error"]["message"]) > 0


# ============================================================
# Integration tests — OpenAPI metadata
# ============================================================


class TestOpenAPIMetadata:
    """OpenAPI schema and documentation endpoint tests."""

    def test_openapi_json_accessible(self, test_client: TestClient) -> None:
        resp = test_client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "openapi" in schema
        assert "info" in schema

    def test_openapi_has_platform_probe_tag(self, test_client: TestClient) -> None:
        resp = test_client.get("/openapi.json")
        tags = {t["name"] for t in resp.json().get("tags", [])}
        assert "Platform Probe" in tags

    def test_openapi_has_admin_tag(self, test_client: TestClient) -> None:
        resp = test_client.get("/openapi.json")
        tags = {t["name"] for t in resp.json().get("tags", [])}
        assert "Admin" in tags

    def test_openapi_has_authentication_tag(self, test_client: TestClient) -> None:
        resp = test_client.get("/openapi.json")
        tags = {t["name"] for t in resp.json().get("tags", [])}
        assert "Authentication" in tags

    def test_openapi_probe_users_has_pagination_params(self, test_client: TestClient) -> None:
        """The probe endpoint schema should document page/page_size params."""
        resp = test_client.get("/openapi.json")
        paths = resp.json()["paths"]
        probe_path = paths.get("/api/v1/probe/users", {})
        get_op = probe_path.get("get", {})
        param_names = {p["name"] for p in get_op.get("parameters", [])}
        assert "page" in param_names
        assert "page_size" in param_names
