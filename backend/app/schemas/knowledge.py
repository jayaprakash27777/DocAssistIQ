from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Literal
import uuid

class KnowledgeReviewRequest(BaseModel):
    new_status: Literal["APPROVED", "REJECTED", "SUPERSEDED", "OUTDATED"]
    superseded_by_id: uuid.UUID | None = None

class KnowledgeEntityResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    status: str
    is_ai_generated: bool
    created_at: datetime | str
    updated_at: datetime | str

    model_config = ConfigDict(from_attributes=True)

class ProvenanceItemResponse(BaseModel):
    id: uuid.UUID
    claim: str
    evidence_grade: str | None
    recommendation_grade: str | None
    is_ai_extracted: bool
    source_name: str
    source_code: str

    model_config = ConfigDict(from_attributes=True)
