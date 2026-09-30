"""DocAssistIQ — Consensus Clinical Criteria & Scoring Schemas."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ClinicalCriteriaEvaluationRequest(BaseModel):
    criteria_name: Optional[str] = Field(
        None,
        description="Specific criteria: 'wells_pe', 'cha2ds2_vasc', 'curb65', 'qsofa', 'centor', 'sle', 'duke', 'myopathy', or None for auto-detection"
    )
    findings: List[str] = Field(default_factory=list, description="Clinical findings, signs, or symptoms")
    labs: Dict[str, Any] = Field(default_factory=dict, description="Laboratory measurements dictionary")


class ClinicalCriteriaItemResult(BaseModel):
    criteria_name: str
    score: int | float
    risk_tier: str
    recommendation: str
    meets_criteria: bool
    fulfilled_items: List[str] = Field(default_factory=list)
    missing_items: Optional[List[str]] = None


class ClinicalCriteriaEvaluationResponse(BaseModel):
    consultation_id: Optional[str] = None
    criteria_results: List[ClinicalCriteriaItemResult]
    safety_disclaimer: str = "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"
