"""DocAssistIQ — Consent Schemas."""

from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ConsentRecordCreate(BaseModel):
    consultation_id: uuid.UUID
    actor_name: str = Field(..., max_length=150)
    actor_relationship: str = Field(..., max_length=50)
    purpose: str = Field(..., max_length=150)
    recording_permitted: bool = False


class ConsentRecordResponse(BaseModel):
    id: uuid.UUID
    consultation_id: uuid.UUID
    actor_name: str
    actor_relationship: str
    consent_text_version: str
    purpose: str
    status: str
    recording_permitted: bool
    recorded_by_id: uuid.UUID
    created_at: Any
    
    model_config = ConfigDict(from_attributes=True)
