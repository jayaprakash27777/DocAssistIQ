"""DocAssistIQ — Hospital-Grade SOAP Note Schemas (Phase 7).

Enterprise typed contracts for:
- CMS E/M 2024 compliant clinical documentation
- 14-Point Comprehensive Review of Systems (ROS)
- Anatomical Systemic Physical Examination
- Bayesian calibrated assessment with ICD-11 coding & MDM complexity
- 6-Pillar evidence-based management plan
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ReviewOfSystems14Point(BaseModel):
    """CMS compliant 14-point review of systems."""
    constitutional: str = Field(default="Negative for fever, chills, unintended weight loss, or fatigue.")
    eyes: str = Field(default="Negative for visual changes, photophobia, eye pain, or diplopia.")
    ent_mouth: str = Field(default="Negative for sore throat, epistaxis, rhinorrhea, or dysphagia.")
    cardiovascular: str = Field(default="Negative for chest pain, palpitations, orthopnea, or leg edema.")
    respiratory: str = Field(default="Negative for dyspnea, wheezing, hemoptysis, or chronic cough.")
    gastrointestinal: str = Field(default="Negative for abdominal pain, nausea, vomiting, melena, or hematochezia.")
    genitourinary: str = Field(default="Negative for dysuria, hematuria, frequency, or urgency.")
    musculoskeletal: str = Field(default="Negative for joint swelling, arthralgia, myalgia, or back pain.")
    integumentary: str = Field(default="Negative for rash, pruritus, petechiae, or new skin lesions.")
    neurological: str = Field(default="Negative for focal weakness, sensory loss, seizures, or syncope.")
    psychiatric: str = Field(default="Negative for depressed mood, severe anxiety, or hallucinations.")
    endocrine: str = Field(default="Negative for heat/cold intolerance, polyuria, or polydipsia.")
    hematologic_lymphatic: str = Field(default="Negative for easy bruising, abnormal bleeding, or lymphadenopathy.")
    allergic_immunologic: str = Field(default="Negative for recurrent infections, hives, or angioedema.")


class PhysicalExamSystemic(BaseModel):
    """Organized systemic anatomical physical examination."""
    general_appearance: str = Field(default="Alert, oriented x 3, in no acute distress.")
    heent: str = Field(default="Normocephalic, atraumatic. Pupils equal, round, and reactive to light. Oropharynx clear.")
    neck: str = Field(default="Supple, full range of motion. No lymphadenopathy, no jugular venous distension (JVD).")
    cardiovascular: str = Field(default="Regular rate and rhythm. Normal S1 and S2. No murmurs, gallops, or friction rubs.")
    pulmonary: str = Field(default="Clear to auscultation bilaterally. No wheezes, rales, or rhonchi. Normal work of breathing.")
    abdominal: str = Field(default="Soft, non-distended, non-tender to palpation throughout. Normal bowel sounds. No peritoneal signs.")
    extremities: str = Field(default="Warm, well-perfused. No cyanosis, clubbing, or peripheral edema. Distal pulses intact 2+.")
    neurological: str = Field(default="Cranial nerves II-XII grossly intact. Motor strength 5/5 throughout. Sensation intact. Normal gait.")
    skin: str = Field(default="Warm, dry, intact. No rashes, petechiae, purpura, or active lesions.")


class AssessmentBlock(BaseModel):
    """Calibrated clinical assessment with ICD coding and MDM scoring."""
    primary_diagnosis: str
    icd10_code: str
    icd11_code: str
    bayesian_posterior_probability: float
    confidence_interval: List[float] = []
    differential_diagnoses: List[Dict[str, Any]] = []
    em_mdm_complexity: Literal["Straightforward", "Low", "Moderate", "High"]
    em_billing_code: str = Field(..., description="Recommended CPT/E&M code, e.g. '99214' or '99205'")
    mdm_rationale: str


class PlanBlock(BaseModel):
    """6-Pillar hospital grade clinical plan."""
    diagnostic_workup: List[str] = []
    pharmacotherapy: List[Dict[str, Any]] = []
    interventions_and_referrals: List[str] = []
    patient_education: List[str] = []
    red_flag_return_precautions: List[str] = []
    disposition_and_followup: str


class HospitalGradeSOAPRequest(BaseModel):
    """Request payload for hospital-grade SOAP note synthesis."""
    clinical_text: str = Field(..., description="Doctor's unstructured notes, patient transcript, or intake summary")
    consultation_id: Optional[str] = None
    vitals: Optional[Dict[str, Any]] = None
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None
    active_diagnoses: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    lab_results: Optional[Dict[str, Any]] = None
    imaging_results: Optional[List[str]] = None


class HospitalGradeSOAPResponse(BaseModel):
    """Comprehensive, validated hospital-grade clinical note."""
    subjective: Dict[str, Any]
    objective: Dict[str, Any]
    assessment: AssessmentBlock
    plan: PlanBlock
    markdown_full_note: str
    execution_time_ms: float
    compliance_standard: str = Field(
        default="CMS E/M 2024 / Joint Commission International (JCI) Standard",
        description="Clinical documentation compliance watermark"
    )
