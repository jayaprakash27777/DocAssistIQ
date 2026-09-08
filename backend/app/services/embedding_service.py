import hashlib
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import EmbeddingRecord
from app.infrastructure.ai.embeddings import get_embedding_provider


def compute_hash(content: str) -> str:
    """Compute a SHA-256 hash of the content to detect changes."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def generate_and_store_embedding(
    db: AsyncSession,
    source_record_id: str,
    source_record_type: str,
    content: str,
) -> Optional[EmbeddingRecord]:
    """
    Generate an embedding for the provided content and store it.
    If an embedding for this content hash already exists for this source,
    it skips regeneration and returns the existing record.
    """
    if not content or not content.strip():
        return None

    content_hash = compute_hash(content)
    provider = get_embedding_provider()

    # 1. Check if we already have an embedding with this exact content hash and model
    existing = await db.scalar(
        select(EmbeddingRecord).where(
            EmbeddingRecord.source_record_id == source_record_id,
            EmbeddingRecord.source_record_type == source_record_type,
            EmbeddingRecord.content_hash == content_hash,
            EmbeddingRecord.embedding_model == provider.model_name
        )
    )
    if existing:
        return existing

    # 2. Generate the embedding vector
    try:
        vector = await provider.generate_embedding(content)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to generate embedding: {e}")
        return None

    # 3. Store the new embedding
    record = EmbeddingRecord(
        source_record_id=source_record_id,
        source_record_type=source_record_type,
        content_hash=content_hash,
        embedding_model=provider.model_name,
        model_version="1.0",  # baseline version
        dimensions=provider.dimensions,
        embedding=vector
    )
    
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    return record
