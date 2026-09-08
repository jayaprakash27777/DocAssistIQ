"""Tests for Phase 30: Clinical Note Generation and OCC."""

import pytest
import uuid
from fastapi.testclient import TestClient
from tests.test_consultations import _register_and_login, _BASE_URL

@pytest.fixture
def auth_headers(test_client: TestClient) -> dict:
    token = _register_and_login(test_client)
    return {"Authorization": f"Bearer {token}"}

def test_occ_update_note(test_client: TestClient, auth_headers: dict):
    # 1. Create a consultation
    res = test_client.post(
        f"{_BASE_URL}/consultations",
        json={"input_text": "Patient has htn and sob."},
        headers=auth_headers
    )
    assert res.status_code == 201
    consultation_id = res.json()["id"]

    # 2. Transition state to "draft" which triggers note generation
    res = test_client.patch(
        f"{_BASE_URL}/consultations/{consultation_id}/status",
        json={"new_status": "draft"},
        headers=auth_headers
    )
    assert res.status_code == 200

    # 3. Fetch note
    res = test_client.get(f"{_BASE_URL}/consultations/{consultation_id}/note", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == 1
    assert data["is_ai_generated"] is True

    # 4. First update (success)
    update_res = test_client.patch(
        f"{_BASE_URL}/consultations/{consultation_id}/note",
        json={
            "version": 1,
            "sections": {"assessment": "Patient is stable."}
        },
        headers=auth_headers
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["version"] == 2
    assert updated_data["is_ai_generated"] is False
    assert updated_data["body"]["assessment"] == "Patient is stable."

    # 5. Second update trying to use stale version 1 (Conflict)
    conflict_res = test_client.patch(
        f"{_BASE_URL}/consultations/{consultation_id}/note",
        json={
            "version": 1,
            "sections": {"plan": "Discharge home."}
        },
        headers=auth_headers
    )
    assert conflict_res.status_code == 409
    body = conflict_res.json()
    # The app uses custom error envelope: {"error": {"code": "...", "message": "..."}}
    assert "Conflict" in body.get("error", {}).get("message", body.get("detail", ""))
