"""DocAssistIQ — Consultation API Integration Tests (Phase 8).

Tests the complete consultation vertical slice through the real API.

Coverage: create, get, list, pagination, ownership, placeholder label,
duplicate submission, direct route access (refresh behavior).
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

_PASSWORD = "ValidPass99"
_BASE_URL = "/api/v1"
_PLACEHOLDER_LABEL = "PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL"

# ── Helpers ───────────────────────────────────────────────────────────────


def _email(prefix: str = "cons") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:6]}@consultation-test.example.com"


def _register_and_login(tc: TestClient, email: str | None = None) -> str:
    email = email or _email()
    tc.post(
        f"{_BASE_URL}/auth/register",
        json={"email": email, "password": _PASSWORD, "full_name": "Dr Test"},
    )
    r = tc.post(
        f"{_BASE_URL}/auth/login",
        json={"email": email, "password": _PASSWORD},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create(
    tc: TestClient,
    token: str,
    text: str = "Patient presents with fever, chills and myalgia for 3 days.",
):
    return tc.post(
        f"{_BASE_URL}/consultations/",
        json={"input_text": text},
        headers=_auth(token),
    )


# ── Create consultation ───────────────────────────────────────────────────


@pytest.mark.integration
def test_create_consultation_success(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    r = _create(test_client, token)
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["status"] == "completed"
    assert body["is_placeholder"] is True
    assert _PLACEHOLDER_LABEL in body["placeholder_response"]
    assert "id" in body
    assert "user_id" in body
    assert "created_at" in body


@pytest.mark.integration
def test_create_consultation_input_too_short(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    r = _create(test_client, token, text="short")  # < 10 chars
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
def test_create_consultation_input_too_long(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    r = _create(test_client, token, text="x" * 10_001)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
def test_create_consultation_unauthenticated(test_client: TestClient) -> None:
    r = test_client.post(
        f"{_BASE_URL}/consultations/",
        json={"input_text": "Patient presents with cough and fever for 5 days."},
    )
    assert r.status_code == 401


@pytest.mark.integration
def test_placeholder_label_always_present(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    r = _create(test_client, token)
    assert r.status_code == 201
    assert r.json()["placeholder_response"].startswith(_PLACEHOLDER_LABEL)


@pytest.mark.integration
def test_is_placeholder_always_true(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    r = _create(test_client, token)
    assert r.status_code == 201
    assert r.json()["is_placeholder"] is True


# ── Get consultation ──────────────────────────────────────────────────────


@pytest.mark.integration
def test_get_own_consultation(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    created = _create(test_client, token)
    assert created.status_code == 201
    consultation_id = created.json()["id"]

    r = test_client.get(
        f"{_BASE_URL}/consultations/{consultation_id}",
        headers=_auth(token),
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["id"] == consultation_id
    assert _PLACEHOLDER_LABEL in body["placeholder_response"]


@pytest.mark.integration
def test_get_other_users_consultation_returns_404(test_client: TestClient) -> None:
    token_a = _register_and_login(test_client)
    token_b = _register_and_login(test_client)

    created = _create(test_client, token_a)
    assert created.status_code == 201
    consultation_id = created.json()["id"]

    r = test_client.get(
        f"{_BASE_URL}/consultations/{consultation_id}",
        headers=_auth(token_b),
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "CONSULTATION_NOT_FOUND"


@pytest.mark.integration
def test_get_nonexistent_consultation_returns_404(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    fake_id = str(uuid.uuid4())
    r = test_client.get(
        f"{_BASE_URL}/consultations/{fake_id}",
        headers=_auth(token),
    )
    assert r.status_code == 404


@pytest.mark.integration
def test_get_consultation_unauthenticated(test_client: TestClient) -> None:
    fake_id = str(uuid.uuid4())
    r = test_client.get(f"{_BASE_URL}/consultations/{fake_id}")
    assert r.status_code == 401


# ── List consultations ────────────────────────────────────────────────────


@pytest.mark.integration
def test_list_consultations_empty(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    r = test_client.get(f"{_BASE_URL}/consultations/", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.integration
def test_list_consultations_shows_own_only(test_client: TestClient) -> None:
    token_a = _register_and_login(test_client)
    token_b = _register_and_login(test_client)

    _create(test_client, token_a)
    _create(test_client, token_a)
    _create(test_client, token_b)  # B's consultation — A should NOT see it

    r = test_client.get(f"{_BASE_URL}/consultations/", headers=_auth(token_a))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.integration
def test_list_consultations_pagination(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    for _ in range(5):
        _create(test_client, token)

    r = test_client.get(
        f"{_BASE_URL}/consultations/?page=1&page_size=3",
        headers=_auth(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert len(body["items"]) == 3
    assert body["pages"] == 2


@pytest.mark.integration
def test_list_consultations_unauthenticated(test_client: TestClient) -> None:
    r = test_client.get(f"{_BASE_URL}/consultations/")
    assert r.status_code == 401


# ── Duplicate submission ──────────────────────────────────────────────────


@pytest.mark.integration
def test_duplicate_submission_creates_two_rows(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    text = "Patient presents with cough and fatigue lasting one week."

    r1 = _create(test_client, token, text=text)
    r2 = _create(test_client, token, text=text)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


# ── Direct route access (refresh) ────────────────────────────────────────


@pytest.mark.integration
def test_direct_route_access_returns_same_data(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    created = _create(test_client, token)
    assert created.status_code == 201

    consultation_id = created.json()["id"]
    post_body = created.json()

    r = test_client.get(
        f"{_BASE_URL}/consultations/{consultation_id}",
        headers=_auth(token),
    )
    assert r.status_code == 200
    get_body = r.json()

    assert get_body["id"] == post_body["id"]
    assert get_body["input_text"] == post_body["input_text"]
    assert get_body["placeholder_response"] == post_body["placeholder_response"]
    assert get_body["status"] == post_body["status"]
