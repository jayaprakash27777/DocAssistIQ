"""DocAssistIQ ?" Model Registry Schema (Phase 65).

Tracks the lifecycle of ML models through strict deployment gates.
"""

from enum import Enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.database import Base


class ModelLifecycleState(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    EVALUATED = "EVALUATED"
    CANDIDATE = "CANDIDATE"
    SAFETY_REVIEW = "SAFETY_REVIEW"
    APPROVED = "APPROVED"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    RETIRED = "RETIRED"


class RegisteredModel(Base):
    __tablename__ = "ml_registered_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Model Metadata
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    base_model: Mapped[str] = mapped_column(String(255), nullable=False)
    adapter_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Pipeline Metadata
    dataset_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evaluation_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # State and Location
    lifecycle_state: Mapped[ModelLifecycleState] = mapped_column(
        SAEnum(ModelLifecycleState), 
        default=ModelLifecycleState.EXPERIMENTAL,
        nullable=False
    )
    artifact_location: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    safety_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Deployment Tracking
    deployment_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rollback_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
