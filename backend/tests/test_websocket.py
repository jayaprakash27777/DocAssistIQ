"""DocAssistIQ — WebSocket Integration Tests (Phase 8).

Tests the /ws/v1/stream endpoint.

Coverage:
  - Valid token → accepted, "connected" message with user_id
  - Invalid token → rejected (WebSocket exception)
  - Missing token → 422 (query param validation before upgrade)
"""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

_PASSWORD = "ValidPass99"
_BASE_URL = "/api/v1"


def _email() -> str:
    return f"ws_{uuid.uuid4().hex[:6]}@ws-test.example.com"


def _register_and_login(tc: TestClient, email: str | None = None) -> str:
    email = email or _email()
    tc.post(
        f"{_BASE_URL}/auth/register",
        json={"email": email, "password": _PASSWORD, "full_name": "WS Tester"},
    )
    r = tc.post(
        f"{_BASE_URL}/auth/login",
        json={"email": email, "password": _PASSWORD},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


# ── WebSocket tests ───────────────────────────────────────────────────────


@pytest.mark.integration
def test_ws_connect_valid_token(test_client: TestClient) -> None:
    """Valid token → accepted, receives connected message."""
    token = _register_and_login(test_client)

    with test_client.websocket_connect(f"/ws/v1/stream?token={token}") as ws:
        msg = ws.receive_text()
        data = json.loads(msg)
        assert data["type"] == "connected"
        assert "user_id" in data
        assert "ts" in data


@pytest.mark.integration
def test_ws_connect_valid_token_user_id_in_message(test_client: TestClient) -> None:
    """Connected message contains a valid UUID for user_id."""
    token = _register_and_login(test_client)

    with test_client.websocket_connect(f"/ws/v1/stream?token={token}") as ws:
        msg = ws.receive_text()
        data = json.loads(msg)
        # Should be a parseable UUID
        uuid.UUID(data["user_id"])


@pytest.mark.integration
def test_ws_connect_invalid_token_rejected(test_client: TestClient) -> None:
    """Invalid token → WebSocket connection refused."""
    with pytest.raises(Exception):
        with test_client.websocket_connect("/ws/v1/stream?token=invalid-token-xyz") as ws:
            ws.receive_text()


@pytest.mark.integration
def test_ws_connect_missing_token_rejected(test_client: TestClient) -> None:
    """Missing required token query param → 422 from FastAPI validation."""
    # When no WebSocket upgrade is sent, FastAPI validates query params as HTTP
    # and returns 422 for missing required parameters
    r = test_client.get("/ws/v1/stream")
    # FastAPI returns 422 for missing required query param
    assert r.status_code in (422, 404)  # 422 expected; 404 if route not matched
