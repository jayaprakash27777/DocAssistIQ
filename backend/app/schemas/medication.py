from typing import List
from pydantic import BaseModel, ConfigDict, Field

class MedicationSuggestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generic_name: str = Field(..., description="Generic name of the medication")
    indication: str = Field(..., description="Clinical indication for this medication")
    formulation: str = Field(..., description="Available or recommended formulation (e.g. tablet, inhaler)")
    route: str = Field(..., description="Route of administration")
    standard_reference_dosing: str = Field(..., description="Standard reference dosing. NOT a patient-specific prescription.")
    contraindications: List[str] = Field(default_factory=list, description="List of contraindications")
    interactions: List[str] = Field(default_factory=list, description="Notable drug interactions")
    allergy_considerations: str = Field(..., description="Allergy considerations")
    renal_considerations: str = Field(..., description="Renal adjustment or considerations")
    hepatic_considerations: str = Field(..., description="Hepatic adjustment or considerations")
    pregnancy_lactation_considerations: str = Field(..., description="Pregnancy and lactation considerations")
    age_considerations: str = Field(..., description="Age-related considerations (e.g., pediatric or geriatric)")
    monitoring_reference_information: str = Field(..., description="Monitoring parameters")
    source_evidence: str = Field(..., description="Reference source")

class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disease: str
    suggestions: List[MedicationSuggestion] = Field(default_factory=list)
