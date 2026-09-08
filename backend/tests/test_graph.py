import uuid
import pytest
from starlette.testclient import TestClient

from app.models.knowledge import (
    Disease, Symptom, Medicine,
    DiseaseSymptom, DiseaseMedicine, MedicineContraindication
)
from tests.test_consultations import _register_and_login, _auth

def test_get_disease_graph_not_found(test_client: TestClient):
    token = _register_and_login(test_client)
    fake_id = str(uuid.uuid4())
    
    response = test_client.get(
        f"/api/v1/knowledge/diseases/{fake_id}/graph",
        headers=_auth(token)
    )
    
    assert response.status_code == 404
