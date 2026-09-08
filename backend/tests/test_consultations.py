import uuid

import pytest
from starlette.testclient import TestClient

_PASSWORD = "ValidPass99"
_BASE_URL = "/api/v1"

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
    token = r.json()["access_token"]
    
    # Create doctor profile so foreign key constraints on consultations don't fail
    r_doc = tc.post(
        f"{_BASE_URL}/doctors/me",
        json={"specialty": "General Practice", "credential_reference": "MD123"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_doc.status_code == 201
    return token

def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

def _create(tc: TestClient, token: str):
    return tc.post(
        f"{_BASE_URL}/consultations",
        json={},
        headers=_auth(token),
    )

# ── Create consultation ───────────────────────────────────────────────────

@pytest.mark.integration
def test_create_consultation_success(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    r = _create(test_client, token)
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["status"] == "created"
    assert "id" in body
    assert "doctor_id" in body
    assert "created_at" in body
    assert body["input_text"] == ""
    assert body["findings"] == []

@pytest.mark.integration
def test_create_consultation_unauthenticated(test_client: TestClient) -> None:
    r = test_client.post(f"{_BASE_URL}/consultations", json={})
    assert r.status_code == 401

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
    assert body["status"] == "created"

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
    r = test_client.get(f"{_BASE_URL}/consultations", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 0

@pytest.mark.integration
def test_list_consultations_shows_own_only(test_client: TestClient) -> None:
    token_a = _register_and_login(test_client)
    token_b = _register_and_login(test_client)

    _create(test_client, token_a)
    _create(test_client, token_a)
    _create(test_client, token_b)  # B's consultation — A should NOT see it

    r = test_client.get(f"{_BASE_URL}/consultations", headers=_auth(token_a))
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2

@pytest.mark.integration
def test_list_consultations_pagination(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    for _ in range(5):
        _create(test_client, token)

    r = test_client.get(
        f"{_BASE_URL}/consultations?limit=3&offset=0",
        headers=_auth(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 3

@pytest.mark.integration
def test_list_consultations_unauthenticated(test_client: TestClient) -> None:
    r = test_client.get(f"{_BASE_URL}/consultations")
    assert r.status_code == 401

# ── Transition status ─────────────────────────────────────────────────────

@pytest.mark.integration
def test_transition_consultation_status(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    created = _create(test_client, token)
    assert created.status_code == 201
    consultation_id = created.json()["id"]

    r = test_client.patch(
        f"{_BASE_URL}/consultations/{consultation_id}/status",
        json={"new_status": "draft", "input_text": "Patient has fever."},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["status"] == "draft"
    assert body["input_text"] == "Patient has fever."

@pytest.mark.integration
def test_clinical_representation(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    created = _create(test_client, token)
    assert created.status_code == 201
    consultation_id = created.json()["id"]

    # First, test we can retrieve an empty representation
    r = test_client.get(
        f"{_BASE_URL}/consultations/{consultation_id}/representation",
        headers=_auth(token),
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["schema_version"] == "1.0"
    assert len(body["symptoms"]) == 0
    
    # We could theoretically add findings and intakes manually here via the db
    # but retrieving it correctly validates the schema structure works.
