import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from pgvector.sqlalchemy import Vector
from app.infrastructure.database import Base

class EmbeddingRecord(Base):
    """
    Stores embeddings for clinical concepts, findings, or sources.
    Tracks model versions and content hashes to avoid redundant generations.
    """
    __tablename__ = "embedding_records"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What was embedded
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_record_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # How it was embedded
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # The actual embedding
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)  # 768 dimensions for nomic-embed-text
    
    # Metadata
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<EmbeddingRecord(id={self.id}, model={self.embedding_model}, type={self.source_record_type})>"
