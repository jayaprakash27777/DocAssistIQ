from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import uuid
from typing import List, Dict, Any

from app.dependencies import get_db, get_current_user
from app.models.embedding import EmbeddingRecord
from app.models.consultation import Consultation
from app.models.user import User
from app.infrastructure.ai.embeddings import get_embedding_provider
from app.schemas.consultation import ConsultationSummary

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/consultations", response_model=List[ConsultationSummary])
async def search_all(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 36: Semantic Patient Search.
    Embeds the user's search query and retrieves the most conceptually similar past consultations.
    """
    try:
        # 1. Embed the search query using the current embedding provider
        provider = get_embedding_provider()
        query_vector = await provider.generate_embedding(q)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Search embedding failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to embed search query")

    user_id = current_user.id
    # 1. Hybrid Search in Vector DBsimilarity search (Cosine Distance) using pgvector
    # We want clinical notes belonging to consultations owned by the requesting user.
    # Note: EmbeddingRecord.embedding.cosine_distance(query_vector) is the sqlalchemy-pgvector syntax
    
    # We join EmbeddingRecord with Consultation
    # Wait, source_record_id is string, so we need to cast or join carefully.
    
    # SQLAlchemy pgvector approach:
    stmt = (
        select(Consultation, EmbeddingRecord.embedding.cosine_distance(query_vector).label("distance"))
        .join(EmbeddingRecord, text("consultations.id::text = embedding_records.source_record_id"))
        .where(Consultation.doctor_id == user_id)
        .where(EmbeddingRecord.source_record_type == "clinical_note")
        .order_by(text("distance ASC"))
        .limit(10)
    )

    result = await db.execute(stmt)
    rows = result.all()
    
    # Map to summary schema, deduplicating consultations that might have multiple embeddings
    summaries = []
    seen_ids = set()
    for row in rows:
        consultation = row[0]
        if consultation.id in seen_ids:
            continue
        seen_ids.add(consultation.id)
        
        # We assume consultation has input_text
        summary = ConsultationSummary(
            id=consultation.id,
            status=consultation.status,
            is_placeholder=False, # This is an actual record
            input_preview=consultation.input_text[:120] if consultation.input_text else "",
            created_at=consultation.created_at
        )
        summaries.append(summary)
        
    return summaries
