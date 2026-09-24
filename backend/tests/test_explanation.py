import uuid
import pytest
from starlette.testclient import TestClient

from app.models.clinical import ClinicalFinding
from tests.test_consultations import _register_and_login, _auth

@pytest.mark.integration
def test_get_finding_explanation_not_found(test_client: TestClient):

    token = _register_and_login(test_client)
    fake_id = str(uuid.uuid4())
    
    response = test_client.get(
        f"/api/v1/explanation/{fake_id}",
        headers=_auth(token)
    )
    
    assert response.status_code == 404
