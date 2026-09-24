"""DocAssistIQ — RAG Retrieval Endpoints.

Supports:
  - High-precision pgvector similarity search against approved clinical evidence in the DB
  - Real-time multi-source medical knowledge engine (PubMed, MedlinePlus, OpenFDA) when requested
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.rag import RAGQueryRequest, RAGResponse, RAGCitation

router = APIRouter(prefix="/rag", tags=["RAG Retrieval"])


@router.post(
    "/query",
    response_model=RAGResponse,
    summary="Evidence-grounded clinical knowledge retrieval",
    responses=API_RESPONSES,
)
async def query_knowledge_base(
    request: RAGQueryRequest,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> RAGResponse:
    """
    Perform Retrieval-Augmented Generation query against the clinical knowledge base.
    1. First searches DB Evidence/Articles via vector similarity.
    2. Strictly obeys `filters.only_approved: True` by returning insufficient_evidence if no approved evidence is in DB.
    3. If DB returns evidence, returns it with citations and provenance.
    4. If DB is empty and `only_approved` is False, falls back to real-time medical sources.
    """
    from app.services.rag_service import retrieve_evidence

    # If filters require approved evidence, strictly use DB retrieval
    if request.filters and request.filters.only_approved:
        return await retrieve_evidence(db, request)

    # Otherwise try DB retrieval first (e.g. ingested PMC articles)
    db_response = await retrieve_evidence(db, request)
    if not db_response.insufficient_evidence and db_response.citations:
        return db_response

    # Fallback to real-time multi-source engine if available and only_approved is False
    try:
        from app.services.realtime_medical_engine import realtime_medical_answer
        result = await realtime_medical_answer(
            query=request.query,
            consultation_id=None,
            top_k=request.top_k or 5,
        )
        citations_out = [
            RAGCitation(
                evidence_id=uuid.uuid4(),
                claim=c.get("excerpt", "") or c.get("claim", ""),
                excerpt=c.get("excerpt", "")[:500],
                source_name=c.get("source_name", "Clinical Source"),
                source_code=c.get("source_type", "literature"),
                source_type=c.get("source_type", "clinical_source"),
                relevance_score=float(c.get("relevance_score", 0.8)),
                url=c.get("url"),
            )
            for c in result.get("citations", [])
        ]
        return RAGResponse(
            query=result.get("query", request.query),
            answer=result.get("answer", ""),
            citations=citations_out,
            confidence_score=result.get("confidence_score", 0.8),
            retrieval_count=result.get("retrieval_count", len(citations_out)),
            fallback_used=result.get("fallback_used", False),
            model_used=result.get("model_used", "DocAssistIQ-MultiSource-v3"),
            data_sources=result.get("data_sources", []),
            insufficient_evidence=len(citations_out) == 0,
        )
    except Exception:
        return db_response
