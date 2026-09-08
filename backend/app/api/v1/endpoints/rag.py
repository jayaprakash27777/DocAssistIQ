"""DocAssistIQ — RAG Retrieval Endpoints (Phase 37).

Endpoints:
  POST /rag/query — Retrieve evidence-grounded answers based on clinical queries.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.rag import RAGQueryRequest, RAGResponse
from app.services.rag_service import retrieve_evidence

router = APIRouter(prefix="/rag", tags=["RAG Retrieval"])

@router.post(
    "/query",
    response_model=RAGResponse,
    summary="Query the clinical knowledge base",
    responses=API_RESPONSES,
)
async def query_knowledge_base(
    request: RAGQueryRequest,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> RAGResponse:
    """
    Perform a Retrieval-Augmented Generation (RAG) query against the knowledge base.
    Strictly filters out superseded/rejected content. Returns citations for provenance.
    """
    # In a real environment with Redis, we would check the cache here using the hash of `request`.
    # E.g. cache_key = f"rag:{hashlib.sha256(request.json().encode()).hexdigest()}"
    # cached = await redis.get(cache_key) ...
    
    response = await retrieve_evidence(db, request)
    return response
