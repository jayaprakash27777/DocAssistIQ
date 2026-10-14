"""DocAssistIQ — Universal Clinical Q&A & Pharmacovigilance Schemas (Phase 6).

Enterprise typed contracts for:
- Universal multi-specialty clinical question answering
- Multi-hop evidence citations and clinical guidelines
- Deterministic pharmacovigilance & adverse drug event discovery
- CYP450 enzyme profiling, QTc stacking, and hemodynamic nephrotoxicity
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ClinicalEvidenceReference(BaseModel):
    """Structured guideline or clinical evidence reference."""
    source: str = Field(..., description="Guideline publisher or authoritative catalog, e.g., 'AHA/ACC', 'KDIGO', 'IDSA'")
    level_of_evidence: str = Field(default="Class I, Level A", description="Evidence hierarchy grade")
    citation_text: str = Field(..., description="Summary of evidence statement")
    url_or_pmid: Optional[str] = Field(default=None, description="PubMed ID or DOI link if available")


class UniversalClinicalQARequest(BaseModel):
    """Clinical question submitted by clinician or AI cockpit."""
    question: str = Field(..., description="Clinical inquiry across any specialty")
    patient_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Patient details (age, sex, vitals, active_diagnoses, current_medications, allergies, eGFR)"
    )
    specialty: Optional[str] = Field(default=None, description="Optional target medical specialty")
    consultation_id: Optional[str] = Field(default=None, description="Consultation ID for record linking")


class PharmacotherapyRegimenItem(BaseModel):
    """Structured medication line in a clinical protocol."""
    drug_name: str
    dose_and_route: str
    frequency: str
    indication: str
    monitoring_parameters: List[str] = []
    renal_adjustment_note: Optional[str] = None


class ClinicalScoreGuidance(BaseModel):
    """Decision rule or risk stratification calculator guidance."""
    score_name: str
    clinical_utility: str
    thresholds_and_actions: Dict[str, str] = {}


class UniversalClinicalQAResponse(BaseModel):
    """Comprehensive, validated response to clinical query."""
    question: str
    specialty: str
    direct_answer: str = Field(..., description="Direct clinical bottom-line answer")
    diagnostic_workup: List[str] = Field(default_factory=list, description="Recommended diagnostic tests, labs, and imaging")
    pharmacotherapy_protocol: List[PharmacotherapyRegimenItem] = Field(default_factory=list, description="Guideline-directed drug regimens")
    contraindications_and_red_flags: List[str] = Field(default_factory=list, description="Critical warning signs & drug contraindications")
    clinical_calculators_or_scores: List[ClinicalScoreGuidance] = Field(default_factory=list, description="Relevant clinical scores")
    evidence_citations: List[ClinicalEvidenceReference] = Field(default_factory=list, description="Authoritative guidelines")
    execution_time_ms: float = Field(..., description="Subsystem computation latency in milliseconds")
    safety_disclaimer: str = Field(
        default="FOR CLINICAL DECISION SUPPORT ONLY — MUST BE VERIFIED BY LICENSED PHYSICIAN",
        description="Mandatory legal & clinical safety watermark"
    )


# ---------------------------------------------------------------------------
# Pharmacovigilance & Polypharmacy Audit Contracts
# ---------------------------------------------------------------------------

class PharmacovigilanceAuditRequest(BaseModel):
    """Request for comprehensive multi-drug pharmacovigilance screening."""
    medications: List[str] = Field(..., description="All concurrent medications to evaluate")
    patient_age: Optional[int] = Field(default=None, description="Patient age in years")
    patient_sex: Optional[str] = Field(default=None, description="Patient sex (Male/Female)")
    is_pregnant: bool = Field(default=False, description="Pregnancy status")
    egfr: Optional[float] = Field(default=None, description="Estimated GFR (mL/min/1.73m2)")
    creatinine: Optional[float] = Field(default=None, description="Serum creatinine (mg/dL)")
    child_pugh_class: Optional[str] = Field(default=None, description="Child-Pugh liver score: 'A', 'B', or 'C'")
    potassium: Optional[float] = Field(default=None, description="Serum potassium (mEq/L)")
    baseline_qtc_ms: Optional[float] = Field(default=None, description="Baseline QTc in milliseconds")
    allergies: Optional[List[str]] = Field(default=None, description="Documented drug allergies")


class CYPEnzymeProfile(BaseModel):
    """CYP450 metabolism pathway profile."""
    inhibitors_present: List[str] = []
    inducers_present: List[str] = []
    substrates_present: List[str] = []
    clinical_consequence: Optional[str] = None


class QTcRiskEvaluation(BaseModel):
    """Cumulative cardiac QTc interval prolongation risk."""
    risk_level: Literal["LOW", "MODERATE", "HIGH", "CRITICAL_TORSADES_ALERT"]
    prolonging_agents: List[str] = []
    cumulative_score: int
    recommendations: List[str] = []


class PharmacovigilanceAuditResponse(BaseModel):
    """Enterprise multi-drug pharmacovigilance audit report."""
    overall_safety_status: Literal["SAFE", "CAUTION", "CRITICAL_HAZARD"]
    total_drugs_analyzed: int
    critical_contraindications: List[Dict[str, Any]] = []
    drug_drug_interactions: List[Dict[str, Any]] = []
    cyp450_profile: Dict[str, CYPEnzymeProfile] = {}
    qtc_prolongation_risk: QTcRiskEvaluation
    triple_whammy_detected: bool = Field(default=False, description="ACEi/ARB + Diuretic + NSAID acute kidney injury hazard")
    serotonin_syndrome_risk: Dict[str, Any] = {}
    bleeding_coagulopathy_risk: Dict[str, Any] = {}
    nephrotoxicity_stacking: Dict[str, Any] = {}
    organ_clearance_adjustments: List[Dict[str, Any]] = []
    beers_criteria_alerts: List[Dict[str, Any]] = []
    anticholinergic_burden: Dict[str, Any] = {}
    execution_time_ms: float
    safety_disclaimer: str = Field(
        default="DETERMINISTIC PHARMACOVIGILANCE AUDIT — VERIFY PRIOR TO ADMINISTRATION",
        description="Mandatory clinical safety watermark"
    )
