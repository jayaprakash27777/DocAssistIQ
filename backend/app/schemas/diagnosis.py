from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.safety import SafetyDecision

class DifferentialDiagnosisItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disease: str
    score: float = Field(..., description="Algorithmic score (NOT a medical probability)")
    supporting_findings: List[str] = Field(default_factory=list)
    missing_expected_findings: List[str] = Field(default_factory=list)
    contradicting_information: List[str] = Field(default_factory=list)
    uncertainty: str = Field(..., description="Qualitative estimate of uncertainty")
    explanation_reference: str = Field(..., description="Explanation of how the algorithm matched this")
    safety_decision: Optional[SafetyDecision] = Field(None, description="Deterministic safety evaluation result")
    geographic_match: bool = Field(default=False, description="True if disease was prioritized based on travel/geographic exposure")
    incubation_fit: Optional[str] = Field(default=None, description="Incubation timeline fit (FITS, TOO_EARLY, TOO_LATE, or None)")
    immediate_tests: List[str] = Field(default_factory=list, description="Top immediate/stat diagnostic tests required for this condition")
    recommended_investigations: List[str] = Field(default_factory=list, description="Recommended laboratory and imaging investigations")
    recommended_medications: List[str] = Field(default_factory=list, description="Guideline-directed medications and pharmacotherapy")
    first_line_treatment: Optional[str] = Field(default=None, description="Immediate first-line management or empiric therapy")

class DifferentialDiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consultation_id: str
    status: Literal["SUCCESS", "INSUFFICIENT_INFO"] = Field(default="SUCCESS")
    message: Optional[str] = Field(None, description="User-friendly message, especially when insufficient info")
    missing_critical_info: List[str] = Field(default_factory=list, description="List of missing clinical parameters preventing analysis")
    provider_metadata: dict = Field(..., description="Metadata about the model/algorithm used")
    top_candidates: List[DifferentialDiagnosisItem] = Field(default_factory=list)
