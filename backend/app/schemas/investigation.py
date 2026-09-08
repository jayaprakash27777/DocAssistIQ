from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class InvestigationSuggestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Name of the investigation (e.g. Chest X-Ray)")
    priority: Literal["HIGH PRIORITY", "CONDITIONAL", "IF INDICATED"] = Field(...)
    rationale: str = Field(..., description="Why this investigation is suggested")
    relevant_clinical_finding: Optional[str] = Field(None, description="Clinical finding triggering this suggestion")
    evidence: str = Field(..., description="Evidence supporting this investigation")
    limitations: str = Field(..., description="Limitations or caveats of this investigation")
    safety_flags: List[str] = Field(default_factory=list, description="Any safety warnings for this test")
    provenance: str = Field(..., description="Source of the guideline")

class InvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disease: str
    suggestions: List[InvestigationSuggestion] = Field(default_factory=list)
