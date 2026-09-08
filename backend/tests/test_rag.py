import pytest
from starlette.testclient import TestClient

from tests.test_consultations import _register_and_login, _auth

def test_rag_query_empty_db(test_client: TestClient):
    """
    Test that the RAG query safely returns insufficient_evidence=True
    when the database has no matching approved evidence.
    """
    token = _register_and_login(test_client)
    
    response = test_client.post(
        "/api/v1/rag/query",
        json={
            "query": "What is the best treatment for acute mountain sickness?",
            "top_k": 3,
            "filters": {
                "only_approved": True
            }
        },
        headers=_auth(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "What is the best treatment for acute mountain sickness?"
    assert data["insufficient_evidence"] is True
    assert len(data["citations"]) == 0
    assert "insufficient clinical evidence" in data["answer"]
