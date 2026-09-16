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

@pytest.mark.asyncio
@pytest.mark.integration
async def test_pmc_ingestion_and_rag_retrieval(int_session, test_client: TestClient):
    """
    Simulates PMC data ingestion and verifies the text generates an embedding
    that is retrievable via vector similarity search in the RAG endpoint.
    """
    from app.services.ingestion.pmc_rag_ingester import pmc_ingester
    from app.models.provenance import Source
    from sqlalchemy import select
    
    # 1. Trigger the ingestion process (mocking the HTTP calls would be better in a real unit test,
    # but here we execute the stub logic we built for testing the DB flows)
    # Since pmc_ingester makes live HTTP requests, for this unit test, we will insert the dummy PMC data directly.
    import uuid
    from app.models.provenance import Article, Evidence
    from app.models.embedding import EmbeddingRecord
    from app.infrastructure.ai.factory import get_embedding_provider
    
    await int_session.begin()
    
    source = Source(
        code="pmc_open_access_test",
        organisation="NIH / NLM",
        name="PubMed Central Open Access",
        access_mechanism="api",
        data_type="literature",
        status="active"
    )
    int_session.add(source)
    await int_session.flush()
    
    article = Article(
        source_id=source.id,
        title="Recent Advances in the Treatment of Severe Sepsis",
        pmid="123456789",
        retrieval_status="indexed"
    )
    int_session.add(article)
    await int_session.flush()
    
    claim_text = "Administration of broad-spectrum antibiotics within 1 hour significantly reduces mortality in severe sepsis."
    evidence = Evidence(
        article_id=article.id,
        entity_type="general",
        entity_id=uuid.uuid4(),
        claim=claim_text,
        evidence_grade="Ia",
        is_ai_extracted=False
    )
    int_session.add(evidence)
    await int_session.flush()
    
    provider = get_embedding_provider()
    vector = await provider.embed(claim_text)
    
    import hashlib
    emb_record = EmbeddingRecord(
        source_record_type="evidence",
        source_record_id=str(evidence.id),
        content_hash=hashlib.sha256(claim_text.encode("utf-8")).hexdigest(),
        embedding_model=provider.metadata.model_name,
        model_version="1.0",
        dimensions=len(vector),
        embedding=vector
    )
    int_session.add(emb_record)
    await int_session.commit()
    
    # 2. Query RAG
    token = _register_and_login(test_client)
    
    response = test_client.post(
        "/api/v1/rag/query",
        json={
            "query": "How quickly should I give antibiotics for sepsis?",
            "top_k": 3,
            "filters": {
                "only_approved": False
            }
        },
        headers=_auth(token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["insufficient_evidence"] is False
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["claim"] == claim_text
