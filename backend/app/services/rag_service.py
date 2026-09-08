import hashlib
import json
import logging
from typing import List, Optional

from sqlalchemy import select, and_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.embedding import EmbeddingRecord
from app.models.provenance import Evidence, Article, Source
from app.models.knowledge import Disease, Symptom, Investigation, Medicine
from app.schemas.rag import RAGQueryRequest, RAGCitation, RAGResponse
from app.infrastructure.ai.embeddings import get_embedding_provider

logger = logging.getLogger(__name__)

# Basic mock answer generation template
def _generate_mock_answer(query: str, citations: List[RAGCitation]) -> str:
    if not citations:
        return ""
    
    answer = f"Based on the retrieved clinical evidence, here is the answer for '{query}':\n\n"
    for idx, cit in enumerate(citations, 1):
        answer += f"[{idx}] {cit.claim} (Grade: {cit.evidence_grade or 'N/A'})\n"
        
    return answer

async def retrieve_evidence(
    db: AsyncSession,
    request: RAGQueryRequest
) -> RAGResponse:
    """
    Core RAG Retrieval pipeline:
    1. Embed query
    2. Retrieve via pgvector (cosine distance)
    3. Join with Evidence/Article/Source
    4. Apply metadata filters (status, credibility)
    5. Mock generative answer
    """
    provider = get_embedding_provider()
    
    # 1. Embed query
    try:
        query_vector = await provider.generate_embedding(request.query)
    except Exception as e:
        logger.error(f"Failed to embed query: {e}")
        return RAGResponse(
            query=request.query,
            answer="System error: Failed to process query.",
            insufficient_evidence=True,
            citations=[]
        )

    # 2. Build the SQLAlchemy query for vector search + joins
    # We want to find Evidence records whose corresponding Entity (Disease, etc.)
    # has a similar embedding, OR the Evidence itself has a similar embedding.
    # For Phase 37, we assume the embedding_records point to `evidence` or the entities.
    # To keep it simple and effective, let's assume `EmbeddingRecord.source_record_id` 
    # matches the `Evidence.id` OR `Evidence.entity_id`.
    # Let's search embeddings, then join Evidence where evidence.id == source_record_id or evidence.entity_id == source_record_id.
    
    # Using cosine distance < 0.5 as an arbitrary threshold for "sufficient" evidence
    distance_col = EmbeddingRecord.embedding.cosine_distance(query_vector).label("distance")
    
    stmt = (
        select(EmbeddingRecord, Evidence, Article, Source, distance_col)
        .join(Evidence, 
              (EmbeddingRecord.source_record_id == cast(Evidence.id, String)) |
              (EmbeddingRecord.source_record_id == cast(Evidence.entity_id, String))
        )
        .join(Article, Evidence.article_id == Article.id)
        .join(Source, Article.source_id == Source.id)
        .where(EmbeddingRecord.embedding_model == provider.model_name)
    )

    # 3. Apply Metadata Filters
    if request.filters.only_approved:
        # We should only return evidence linked to entities that are APPROVED.
        # However, checking polymorphic entities in SQL is complex.
        # For simplicity, we assume Evidence itself must have been reviewed by a human if extracted by AI.
        stmt = stmt.where(
            and_(
                Evidence.is_ai_extracted == False, # or
                Evidence.reviewed_by_id != None
            )
        )
        
    if request.filters.min_evidence_grade:
        # Simplistic grade filtering (exact match for now, could be hierarchical)
        stmt = stmt.where(Evidence.evidence_grade == request.filters.min_evidence_grade)

    # Order by nearest neighbor
    stmt = stmt.order_by(distance_col).limit(request.top_k)

    result = await db.execute(stmt)
    rows = result.all()

    # 4. Reranking / Post-processing
    citations: List[RAGCitation] = []
    seen_evidence = set()
    
    for emb, ev, art, src, dist in rows:
        # Baseline threshold: if the nearest neighbor is too far, we consider it insufficient.
        # Note: text-embedding-3-small mock generates random vectors, so distance might be random.
        # But we still enforce a structure.
        if dist > 0.8:  # If distance is too high, ignore it
            continue
            
        if ev.id in seen_evidence:
            continue
            
        seen_evidence.add(ev.id)
        citations.append(
            RAGCitation(
                evidence_id=ev.id,
                claim=ev.claim,
                evidence_grade=ev.evidence_grade,
                recommendation_grade=ev.recommendation_grade,
                source_name=src.name,
                source_code=src.code,
                article_doi=art.doi,
                entity_code=str(ev.entity_id)
            )
        )

    # 5. Citation validation and generative response
    insufficient = len(citations) == 0
    answer = "I'm sorry, but there is insufficient clinical evidence in the approved knowledge base to answer this query safely." if insufficient else _generate_mock_answer(request.query, citations)

    return RAGResponse(
        query=request.query,
        answer=answer,
        insufficient_evidence=insufficient,
        citations=citations
    )
