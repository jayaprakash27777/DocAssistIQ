"""
DocAssistIQ - Enterprise Red Team Clinical Safety & Counterfactual Schemas
Phase 9: High-assurance safety guardrails, fatal contraindication traps, and counterfactual mimic audits.
Zero faking, zero mocking. Sub-millisecond deterministic clinical protection.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ContraindicationTrapDetail(BaseModel):
    """Detailed record of an intercepted fatal clinical trap."""
    trap_id: str = Field(..., description="Unique clinical trap identifier, e.g. 'TRAP-WPW-AVBLOCKER'")
    severity: str = Field(..., description="'FATAL_HAZARD', 'SEVERE_HARM', 'CRITICAL_CONTRAINDICATION'")
    interception_status: str = Field("BLOCKED_AND_PREVENTED", description="'BLOCKED_AND_PREVENTED' or 'WARNING_RAISED'")
    pathophysiology: str = Field(..., description="Medical mechanism of toxicity, decompensation, or mortality")
    offending_agents: List[str] = Field(default_factory=list, description="Specific drugs, procedures, or orders that triggered trap")
    trigger_condition: str = Field(..., description="Underlying or suspected clinical condition creating vulnerability")
    corrective_alternative: str = Field(..., description="Guideline-directed lifesaving alternative therapy")


class CounterfactualMimicAudit(BaseModel):
    """Comparative audit against high-mortality clinical mimic presentations."""
    primary_condition: str = Field(..., description="Working or suspected primary diagnosis")
    fatal_mimic_condition: str = Field(..., description="High-risk lethal mimic that presents identically")
    minimal_differentiating_findings: List[str] = Field(default_factory=list, description="Subtle hallmark findings that separate the two conditions")
    misdiagnosis_risk: str = Field("EXTREME", description="'EXTREME', 'HIGH', 'MODERATE'")
    mandatory_rule_out_action: str = Field(..., description="Diagnostic test or clinical action mandated before irreversible therapy")
    mimic_excluded: bool = Field(False, description="Whether the mimic has been explicitly excluded in the presentation")


class SafetyGuardrailCheckRequest(BaseModel):
    """Input payload to evaluate clinical decisions against red-team safety guardrails."""
    patient_id: Optional[str] = Field("P-GUARDRAIL", description="Patient identifier")
    clinical_scenario: str = Field(..., description="Unstructured clinical presentation narrative, complaints, exam")
    suspected_or_primary_condition: str = Field(..., description="Primary suspected diagnosis (e.g. 'WPW Syndrome', 'Aortic Dissection')")
    proposed_interventions: List[str] = Field(default_factory=list, description="Proposed non-pharmacologic interventions or procedures")
    proposed_medications: List[str] = Field(default_factory=list, description="Proposed medications, dosages, or infusions")
    differential_diagnoses: List[str] = Field(default_factory=list, description="Working differential diagnosis list")
    vital_signs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Current vital signs (HR, BP, SpO2, etc.)")
    physical_findings: Optional[List[str]] = Field(default_factory=list, description="Confirmed physical examination signs")
    known_conditions: Optional[List[str]] = Field(default_factory=list, description="Comorbidities, past medical history")


class SafetyGuardrailAuditResponse(BaseModel):
    """Complete deterministic safety audit with blocked fatal hazards and certified actions."""
    is_safe: bool = Field(..., description="True if no fatal hazards or severe harm contraindications were detected")
    overall_safety_tier: str = Field(..., description="'CERTIFIED_SAFE', 'WARNING_ISSUED', 'FATAL_HAZARD_BLOCKED'")
    fatal_hazard_intercepted: bool = Field(..., description="True if a lethal medical error was actively blocked")
    contraindication_traps_triggered: List[ContraindicationTrapDetail] = Field(default_factory=list, description="List of intercepted fatal contraindication traps")
    counterfactual_mimic_audits: List[CounterfactualMimicAudit] = Field(default_factory=list, description="Counterfactual lethal mimic differential audits")
    mandatory_rule_outs: List[str] = Field(default_factory=list, description="Mandatory tests to perform prior to committing to treatment")
    blocked_interventions: List[str] = Field(default_factory=list, description="Prescriptions or procedures removed from the clinical plan for safety")
    certified_safe_interventions: List[str] = Field(default_factory=list, description="Interventions verified to be safe under current physiology")
    corrected_clinical_plan: List[str] = Field(default_factory=list, description="Lifesaving corrected management plan")
    guardrail_execution_time_ms: float = Field(..., description="Deterministic execution latency in milliseconds")
    audit_summary: str = Field(..., description="Executive safety summary and rationale")
