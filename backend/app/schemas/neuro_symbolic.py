"""DocAssistIQ — Neuro-Symbolic Clinical Architecture Typed Foundation.

Unified data contracts and mathematical structures for:
1. Probabilistic Bayesian Inference & Likelihood Ratios
2. Information-Theoretic Discriminative Test Selection (Shannon Entropy)
3. Multi-Hop Evidence & NLI Entailment Verification
4. Real-time Speculative Streaming Chunks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EvidenceCategory(str, Enum):
    SYMPTOM = "symptom"
    PHYSICAL_SIGN = "physical_sign"
    VITAL_SIGN = "vital_sign"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    EPIDEMIOLOGICAL = "epidemiological"
    TEMPORAL = "temporal"


class EvidencePolarity(str, Enum):
    CONFIRMED_PRESENT = "confirmed_present"
    CONFIRMED_ABSENT = "confirmed_absent"
    UNKNOWN = "unknown"


class DiagnosticTriageLevel(str, Enum):
    CRITICAL_EMERGENCY = "CRITICAL_EMERGENCY"   # Stat action needed within 15 mins (e.g. STEMI, Aortic Dissection)
    EMERGENT = "EMERGENT"                       # Evaluation needed within 1 hour (e.g. Sepsis, Acute Appendicitis)
    URGENT = "URGENT"                           # Evaluation needed within 4 hours (e.g. Pyelonephritis, Cellulitis)
    ROUTINE = "ROUTINE"                         # Outpatient management appropriate


class NLIEntailmentStatus(str, Enum):
    ENTAILMENT = "ENTAILMENT"       # Supported directly by ground-truth evidence
    NEUTRAL = "NEUTRAL"             # Plausible but unverified claim (flagged/pruned)
    CONTRADICTION = "CONTRADICTION" # Factually conflicts with clinical evidence (strictly blocked)


class BayesianEvidenceToken(BaseModel):
    """Normalized clinical finding with epidemiological sensitivity/specificity values."""
    model_config = ConfigDict(frozen=True)

    concept_id: str = Field(..., description="Canonical concept identifier (e.g. SNOMED-CT or CUI)")
    name: str = Field(..., description="Standardized clinical term")
    category: EvidenceCategory = Field(default=EvidenceCategory.SYMPTOM)
    polarity: EvidencePolarity = Field(default=EvidencePolarity.CONFIRMED_PRESENT)
    onset_days_ago: Optional[float] = Field(default=None, description="Time delta since symptom onset")
    severity_weight: float = Field(default=1.0, ge=0.1, le=5.0)
    raw_text: Optional[str] = Field(default=None)


class EntropyDiscriminativeTest(BaseModel):
    """Diagnostic test evaluated by mutual information gain to separate top differential candidates."""
    test_name: str
    target_conditions: List[str]
    entropy_reduction_bits: float = Field(..., description="Expected Shannon entropy reduction")
    expected_positive_implication: str
    expected_negative_implication: str
    urgency: str = Field(default="STAT", description="STAT | URGENT | ROUTINE")
    estimated_turnaround_time: str = Field(default="30-60 mins")


class BayesianCandidate(BaseModel):
    """Mathematically verified disease candidate scored via Bayesian likelihood ratios."""
    disease_id: str
    disease_name: str
    icd11_code: Optional[str] = None
    snomed_ct: Optional[str] = None
    category: str = "General Medicine"
    
    # Probabilistic Reasoning Metrics
    pre_test_probability: float = Field(..., ge=0.0, le=1.0)
    positive_likelihood_ratio: float = Field(..., ge=0.0, description="Compound LR+ calculated from confirmed findings")
    negative_likelihood_ratio: float = Field(..., ge=0.0, description="Compound LR- calculated from absent expected findings")
    post_test_probability: float = Field(..., ge=0.0, le=1.0, description="Mathematically calculated post-test odds converted to probability")
    confidence_interval: List[float] = Field(default_factory=lambda: [0.0, 1.0])
    
    # Evidence Grounding
    supporting_evidence: List[str] = Field(default_factory=list)
    missing_expected_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    discriminative_tests: List[EntropyDiscriminativeTest] = Field(default_factory=list)
    
    # Safety & Triage
    triage_level: DiagnosticTriageLevel = Field(default=DiagnosticTriageLevel.ROUTINE)
    is_must_not_miss: bool = Field(default=False, description="True if condition is life-threatening/fatal if untreated")
    emergency_warning: Optional[str] = None
    first_line_management: Optional[str] = None
    recommended_medications: List[str] = Field(default_factory=list)


class ClinicalReasoningTrace(BaseModel):
    """Transparent audit trace of the neuro-symbolic reasoning pipeline."""
    consultation_id: str
    execution_time_ms: float
    total_diseases_evaluated: int
    symbolic_retrieval_ms: float
    bayesian_inference_ms: float
    neural_synthesis_ms: float
    nli_verification_ms: float
    hypotheses_generated: int
    hypotheses_pruned_by_negation: int
    hypotheses_surviving: int
    nli_claims_verified: int
    nli_claims_rejected: int
    model_version: str = "DocAssistIQ-NeuroSymbolic-v1"


class StreamingDiagnosisChunk(BaseModel):
    """Server-Sent Event (SSE) payload for real-time progressive diagnostic streaming."""
    event_type: str = Field(..., description="start | candidate | test | narrative_token | end | error")
    consultation_id: str
    sequence_id: int
    token: Optional[str] = None
    candidate: Optional[BayesianCandidate] = None
    payload: Optional[Dict[str, Any]] = None
    elapsed_ms: Optional[float] = None
    reasoning_trace: Optional[ClinicalReasoningTrace] = None
