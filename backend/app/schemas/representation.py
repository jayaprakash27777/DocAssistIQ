from __future__ import annotations

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.safety import SafetyDecision

class Provenance(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_type: str = Field(..., description="'manual_intake', 'transcript', 'clinical_finding', 'clinical_note'")
    source_id: str | uuid.UUID
    timestamp: datetime
    author_id: str | uuid.UUID | None = None

class RepresentationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: str
    concept: str | None = None
    status: str | None = None
    provenances: List[Provenance] = Field(default_factory=list)

class PatientContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    demographics: str | None = None
    provenances: List[Provenance] = Field(default_factory=list)

class ClinicalRepresentationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consultation_id: uuid.UUID
    schema_version: str = "1.0"
    generated_at: datetime
    
    patient_context: PatientContext
    symptoms: List[RepresentationItem] = Field(default_factory=list)
    negations: List[RepresentationItem] = Field(default_factory=list)
    duration: List[RepresentationItem] = Field(default_factory=list)
    severity: List[RepresentationItem] = Field(default_factory=list)
    history: List[RepresentationItem] = Field(default_factory=list)
    travel_history: List[RepresentationItem] = Field(default_factory=list)
    medications: List[RepresentationItem] = Field(default_factory=list)
    allergies: List[RepresentationItem] = Field(default_factory=list)
    vitals: List[RepresentationItem] = Field(default_factory=list)
    investigations: List[RepresentationItem] = Field(default_factory=list)
    report_findings: List[RepresentationItem] = Field(default_factory=list)
    
    safety_decision: Optional[SafetyDecision] = Field(None, description="Red flag safety evaluation result")
