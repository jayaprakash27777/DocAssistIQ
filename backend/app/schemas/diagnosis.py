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
    is_outbreak_match: bool = Field(default=False, description="True if matched active state or global epidemic surveillance")
    outbreak_badge: Optional[str] = Field(default=None, description="Outbreak alert banner text")
    outbreak_details: Optional[dict] = Field(default=None, description="Detailed outbreak alert payload")
    icd11_code: Optional[str] = Field(default=None, description="WHO ICD-11 Linearization Code from Clinical Gateway")
    snomed_ct: Optional[str] = Field(default=None, description="SNOMED CT Concept ID from UMLS Gateway")
    mondo_id: Optional[str] = Field(default=None, description="MONDO Disease Ontology Identifier")
    hpo_phenotypes: List[str] = Field(default_factory=list, description="Human Phenotype Ontology (HPO) matched terms")
    clinical_trials: List[dict] = Field(default_factory=list, description="Active trials from ClinicalTrials.gov v2 REST API")
    europe_pmc_citations: List[dict] = Field(default_factory=list, description="Open-access literature from Europe PMC")
    boxed_warning_alert: Optional[str] = Field(default=None, description="FDA Boxed Warning alert from openFDA")
    clinical_gateway_verified: bool = Field(default=False, description="True if verified across 52+ authoritative gateways")

class DifferentialDiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consultation_id: str
    status: Literal["SUCCESS", "INSUFFICIENT_INFO"] = Field(default="SUCCESS")
    message: Optional[str] = Field(None, description="User-friendly message, especially when insufficient info")
    missing_critical_info: List[str] = Field(default_factory=list, description="List of missing clinical parameters preventing analysis")
    provider_metadata: dict = Field(..., description="Metadata about the model/algorithm used")
    top_candidates: List[DifferentialDiagnosisItem] = Field(default_factory=list)
    outbreak_detected: bool = Field(default=False, description="True if symptoms match an active state or global outbreak")
    outbreak_matches: List[dict] = Field(default_factory=list, description="Matched state or global outbreak alerts")
    outbreak_summary: Optional[str] = Field(default=None, description="Clinical summary of active outbreak matches")
    clinical_gateway_52_sources: Optional[str] = Field(default="ACTIVE", description="52+ Authoritative Clinical Gateways Status")
    active_knowledge_sources: List[str] = Field(default_factory=list, description="List of active knowledge source APIs queried")
    hpo_phenotype_matches: List[dict] = Field(default_factory=list, description="Monarch Human Phenotype Ontology matches")
    rare_disease_matches: List[dict] = Field(default_factory=list, description="Orphanet / ORDO rare disease registry matches")

