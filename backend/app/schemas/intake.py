"""DocAssistIQ — Manual Intake Schemas (Phase 22)."""

from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ManualIntakeUpdate(BaseModel):
    chief_complaint: str | None = None
    symptoms: str | None = None
    duration: str | None = None
    severity: str | None = None
    onset: str | None = None
    location: str | None = None
    associated_symptoms: str | None = None
    aggravating_factors: str | None = None
    relieving_factors: str | None = None
    negations: str | None = None
    past_medical_history: str | None = None
    medications: str | None = None
    allergies: str | None = None
    family_social_history: str | None = None
    vitals: str | None = None
    previous_investigations: str | None = None


class ManualIntakeResponse(BaseModel):
    id: uuid.UUID
    consultation_id: uuid.UUID
    doctor_id: uuid.UUID
    status: str
    
    chief_complaint: str | None
    symptoms: str | None
    duration: str | None
    severity: str | None
    onset: str | None
    location: str | None
    associated_symptoms: str | None
    aggravating_factors: str | None
    relieving_factors: str | None
    negations: str | None
    
    past_medical_history: str | None
    medications: str | None
    allergies: str | None
    family_social_history: str | None
    vitals: str | None
    previous_investigations: str | None
    
    created_at: Any
    updated_at: Any
    
    model_config = ConfigDict(from_attributes=True)
