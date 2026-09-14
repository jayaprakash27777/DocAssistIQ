from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class PolypharmacyRequest(BaseModel):
    proposed_medications: List[str] = Field(..., description="List of medications the doctor is considering prescribing")

class InteractionDetail(BaseModel):
    severity: Literal["CRITICAL", "WARNING", "MINOR", "SAFE"] = Field(..., description="Severity of the interaction")
    drugs_involved: List[str] = Field(..., description="The specific drugs involved in this interaction")
    mechanism: str = Field(..., description="Pharmacokinetic or pharmacodynamic mechanism (e.g., CYP3A4 inhibition)")
    clinical_effect: str = Field(..., description="What happens to the patient clinically (e.g., increased risk of bleeding)")
    recommendation: str = Field(..., description="Actionable advice (e.g., reduce dose by 50%, avoid combination)")

class PolypharmacyResponse(BaseModel):
    interactions: List[InteractionDetail] = Field(default_factory=list)
    summary_assessment: str = Field(..., description="Overall summary of the safety profile")
    is_safe: bool = Field(..., description="True if there are no CRITICAL interactions")
