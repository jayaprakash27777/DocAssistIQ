import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PatientProfileCreate(BaseModel):
    patient_ref: str = Field(..., description="Opaque external reference from EMR/HIS")
    age_group: str | None = Field(None, description="Pseudo-demographic: e.g., '18-25'")
    biological_sex: str | None = Field(None, description="Biological sex")
    baseline_conditions: dict[str, Any] = Field(default_factory=dict, description="JSON containing known conditions")


class PatientProfileUpdate(BaseModel):
    age_group: str | None = None
    biological_sex: str | None = None
    baseline_conditions: dict[str, Any] | None = None


class PatientSessionResponse(BaseModel):
    id: uuid.UUID
    patient_ref: str
    encounter_type: str
    status: str
    clinical_notes_summary: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientProfileResponse(BaseModel):
    id: uuid.UUID
    patient_ref: str
    age_group: str | None = None
    biological_sex: str | None = None
    baseline_conditions: dict[str, Any]
    sessions: list[PatientSessionResponse] = []

    model_config = ConfigDict(from_attributes=True)
