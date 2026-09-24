import uuid
import pytest
from starlette.testclient import TestClient

from app.models.provenance import Evidence, Article, Source
from tests.test_consultations import _register_and_login, _auth

@pytest.mark.integration
def test_verify_claim_fabricated_id(test_client: TestClient):

    token = _register_and_login(test_client)
    fake_id = str(uuid.uuid4())
    
    response = test_client.post(
        "/api/v1/verification/verify",
        json={
            "evidence_id": fake_id,
            "claim_text": "Aspirin is used for headaches."
        },
        headers=_auth(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] is False
    assert data["status"] == "FABRICATED_ID"
