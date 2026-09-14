import uuid
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class ClinicianFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Stores explicit feedback from clinicians on AI suggestions.
    This data is governed evaluation data, not used for automatic online retraining.
    """
    __tablename__ = "clinician_feedback"

    suggestion_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Unique identifier for the suggestion being evaluated"
    )
    
    suggestion_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="e.g., 'clinical_note', 'diagnosis', 'investigation', 'medication'"
    )
    
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False
    )
    
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'ACCEPT', 'MODIFY', 'REJECT'"
    )
    
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Clinician's explanation for their decision"
    )
    
    suggestion_context: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="The exact JSON payload that was suggested"
    )
    
    modified_context: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="The exact JSON payload after clinician modification (if decision=MODIFY)"
    )
    
    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default="1.0.0",
        comment="Version of the LLM/Embedding model used"
    )
    
    knowledge_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default="1.0.0",
        comment="Hash or version of the Knowledge Graph at the time"
    )
