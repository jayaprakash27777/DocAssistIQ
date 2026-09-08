import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from pgvector.sqlalchemy import Vector
from app.infrastructure.database import Base

class EmbeddingRecord(Base):
    """
    Stores embeddings for clinical concepts, findings, or sources.
    Tracks model versions and content hashes to avoid redundant generations.
    """
    __tablename__ = "embedding_records"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What was embedded
    source_record_id = Column(String(255), nullable=False, index=True)
    source_record_type = Column(String(100), nullable=False, index=True)
    content_hash = Column(String(255), nullable=False, index=True)
    
    # How it was embedded
    embedding_model = Column(String(100), nullable=False)
    model_version = Column(String(100), nullable=False)
    dimensions = Column(Integer, nullable=False)
    
    # The actual embedding
    embedding = Column(Vector(1536), nullable=False)  # 1536 dimensions is standard for text-embedding-3-small
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<EmbeddingRecord(id={self.id}, model={self.embedding_model}, type={self.source_record_type})>"
