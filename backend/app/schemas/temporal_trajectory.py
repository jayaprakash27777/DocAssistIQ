"""
DocAssistIQ - Enterprise Temporal Trajectory & Clinical Timeline Delta Schemas
Phase 8: High-precision mathematical time-series modeling for acute and longitudinal clinical trajectories.
Zero mocking, zero faking. Full RCP NEWS2, Shock Index, KDIGO AKI, and Sepsis-3 qSOFA adherence.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VitalSignObservation(BaseModel):
    """Single time-stamped clinical vital signs observation."""
    timestamp: str = Field(..., description="ISO 8601 or clinical encounter timestamp, e.g. '2026-10-14T08:00:00Z'")
    heart_rate: Optional[int] = Field(None, ge=20, le=300, description="Pulse rate in beats per minute (bpm)")
    systolic_bp: Optional[int] = Field(None, ge=30, le=300, description="Systolic blood pressure in mmHg")
    diastolic_bp: Optional[int] = Field(None, ge=20, le=200, description="Diastolic blood pressure in mmHg")
    respiratory_rate: Optional[int] = Field(None, ge=4, le=80, description="Respiratory rate in breaths per minute")
    temperature_c: Optional[float] = Field(None, ge=28.0, le=45.0, description="Body temperature in degrees Celsius")
    spo2_percent: Optional[float] = Field(None, ge=40.0, le=100.0, description="Oxygen saturation SpO2 percentage")
    on_supplemental_o2: bool = Field(False, description="Whether patient is receiving supplemental oxygen therapy")
    avpu_consciousness: str = Field("Alert", description="Consciousness level: 'Alert', 'Voice', 'Pain', 'Unresponsive'")


class LabObservation(BaseModel):
    """Single time-stamped clinical laboratory observation."""
    timestamp: str = Field(..., description="Lab draw timestamp, e.g. '2026-10-14T08:00:00Z'")
    creatinine_mg_dl: Optional[float] = Field(None, ge=0.1, le=30.0, description="Serum creatinine in mg/dL")
    troponin_ng_ml: Optional[float] = Field(None, ge=0.0, le=500.0, description="High-sensitivity Cardiac Troponin (hs-cTn) in ng/mL or ug/L")
    lactate_mmol_l: Optional[float] = Field(None, ge=0.1, le=30.0, description="Serum / arterial lactate in mmol/L")
    platelets_k_ul: Optional[float] = Field(None, ge=1.0, le=2000.0, description="Platelet count in x10^3/uL")
    wbc_k_ul: Optional[float] = Field(None, ge=0.1, le=150.0, description="White blood cell count in x10^3/uL")
    crp_mg_l: Optional[float] = Field(None, ge=0.0, le=500.0, description="C-Reactive Protein in mg/L")
    hemoglobin_g_dl: Optional[float] = Field(None, ge=1.0, le=25.0, description="Hemoglobin in g/dL")
    potassium_mmol_l: Optional[float] = Field(None, ge=1.0, le=10.0, description="Serum potassium in mmol/L")
    bicarbonate_mmol_l: Optional[float] = Field(None, ge=1.0, le=60.0, description="Serum bicarbonate (HCO3-) in mmol/L")
    blood_glucose_mg_dl: Optional[float] = Field(None, ge=10.0, le=1500.0, description="Blood glucose in mg/dL")


class SymptomObservation(BaseModel):
    """Single time-stamped subjective or observed clinical manifestation."""
    timestamp: str = Field(..., description="Timestamp of symptom record")
    symptom: str = Field(..., description="Clinical symptom or sign name")
    severity_1_to_10: int = Field(5, ge=1, le=10, description="Self-reported or assessed severity on 1-10 numeric scale")
    status: str = Field("PERSISTENT", description="'NEW', 'WORSENING', 'PERSISTENT', 'IMPROVING', 'RESOLVED'")
    anatomical_location: Optional[str] = Field(None, description="Anatomical location or migration target")
    notes: Optional[str] = Field(None, description="Clinical contextual notes")


class ClinicalIntervention(BaseModel):
    """Clinical therapy, medication, or procedural intervention executed along timeline."""
    timestamp: str = Field(..., description="Intervention timestamp")
    intervention_type: str = Field(..., description="'FLUID_BOLUS', 'VASOPRESSOR', 'ANTIBIOTIC', 'OXYGEN_THERAPY', 'INTUBATION', 'SURGERY', 'DIALYSIS', 'MEDICATION', 'MONITORING'")
    description: str = Field(..., description="Description of the intervention")
    dose_or_rate: Optional[str] = Field(None, description="Dosing, infusion rate, or parameter")


class EarlyWarningScoreDetail(BaseModel):
    """Mathematical National Early Warning Score 2 (NEWS2) calculation."""
    score_name: str = "NEWS2"
    total_score: int = Field(..., ge=0, le=20, description="Total aggregate NEWS2 score")
    risk_level: str = Field(..., description="'LOW', 'LOW_MEDIUM', 'MEDIUM', 'HIGH'")
    clinical_action: str = Field(..., description="Royal College of Physicians recommended clinical action")
    subscores: Dict[str, int] = Field(default_factory=dict, description="Component subscores per physiologic parameter")
    has_extreme_subscore: bool = Field(False, description="True if any single parameter scores 3 (red trigger)")


class ShockIndexDetail(BaseModel):
    """Physiological Shock Index (Heart Rate / Systolic BP)."""
    value: float = Field(..., description="Calculated Shock Index (HR / SBP)")
    classification: str = Field(..., description="'NORMAL', 'MILD_ELEVATION', 'OCCULT_SHOCK', 'SEVERE_SHOCK'")
    interpretation: str = Field(..., description="Hemodynamic interpretation and occult hypoperfusion risk")
    is_elevated: bool = Field(..., description="True if shock index exceeds 0.70")


class LabDeltaMetric(BaseModel):
    """Serial laboratory kinetic delta, velocity of change, and clinical significance."""
    parameter: str = Field(..., description="Lab parameter name (e.g. 'Creatinine', 'Troponin', 'Lactate')")
    baseline_value: float = Field(..., description="Earliest or reference laboratory measurement")
    current_value: float = Field(..., description="Most recent laboratory measurement")
    absolute_delta: float = Field(..., description="current_value - baseline_value")
    relative_percent_change: float = Field(..., description="Percentage change relative to baseline")
    time_interval_hours: float = Field(..., ge=0.0, description="Elapsed time between measurements in hours")
    velocity_per_hour: float = Field(..., description="Rate of change per hour")
    clinical_significance: str = Field(..., description="Clinical interpretation (e.g. KDIGO Stage 1 AKI, Myocardial Infarction delta)")
    is_critical: bool = Field(False, description="Flagged true if delta crosses life-threatening threshold")


class TrajectoryForecast(BaseModel):
    """Predictive trajectory projection across 6h, 12h, 24h horizons."""
    trajectory_direction: str = Field(..., description="'RAPIDLY_DETERIORATING', 'DETERIORATING', 'STABLE', 'IMPROVING', 'RAPIDLY_IMPROVING'")
    clinical_phase: str = Field(..., description="'EARLY_INSULT', 'COMPENSATING', 'ACUTE_DECOMPENSATION', 'REFRACTORY_SHOCK', 'RECOVERY', 'STABLE_MAINTENANCE'")
    decompensation_hazard_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated composite hazard score between 0.0 and 1.0")
    icu_transfer_recommended: bool = Field(False, description="Recommendation for Critical Care / ICU consultation")
    rapid_response_team_alert: bool = Field(False, description="Recommendation to activate Rapid Response Team (RRT)")
    predicted_milestones_24h: List[str] = Field(default_factory=list, description="Projected clinical milestones if current trend continues")
    recommended_urgent_interventions: List[str] = Field(default_factory=list, description="Immediate corrective actions to halt decompensation")
    rationale: str = Field(..., description="Physiological explanation of projected trajectory")


class ChronologicalMilestoneEvent(BaseModel):
    """Unified chronological clinical milestone event for timeline visualization."""
    timestamp: str
    event_type: str = Field(..., description="'VITAL_SIGN', 'LABORATORY', 'SYMPTOM_CHANGE', 'INTERVENTION', 'ALERT'")
    title: str
    description: str
    severity: str = Field("INFO", description="'INFO', 'WARNING', 'CRITICAL', 'RECOVERY'")
    details: Dict[str, Any] = Field(default_factory=dict)


class TemporalTrajectoryRequest(BaseModel):
    """Patient longitudinal and serial observation input payload."""
    patient_id: Optional[str] = Field("P-LONGITUDINAL", description="Patient identifier")
    age: Optional[int] = Field(55, ge=0, le=125, description="Patient age in years")
    sex: Optional[str] = Field("unspecified", description="'male', 'female', or 'unspecified'")
    primary_diagnosis_suspicion: Optional[str] = Field(None, description="Suspected primary condition under evaluation")
    vitals_timeline: List[VitalSignObservation] = Field(default_factory=list, description="Serial vital sign observations ordered chronologically")
    labs_timeline: List[LabObservation] = Field(default_factory=list, description="Serial laboratory observations ordered chronologically")
    symptoms_timeline: List[SymptomObservation] = Field(default_factory=list, description="Serial symptom status observations")
    interventions_timeline: List[ClinicalIntervention] = Field(default_factory=list, description="Interventions executed along timeline")


class TemporalTrajectoryResponse(BaseModel):
    """Complete mathematical trajectory analysis, early warning scores, and predictive forecast."""
    patient_id: str
    evaluation_timestamp: str
    total_observations_analyzed: int
    news2_current: EarlyWarningScoreDetail
    news2_delta: Optional[int] = Field(None, description="Delta in NEWS2 score between earliest and latest vital observation")
    shock_index: ShockIndexDetail
    qsofa_score: int = Field(..., ge=0, le=3, description="Sepsis-3 Quick SOFA score (0-3)")
    qsofa_high_risk: bool = Field(..., description="True if qSOFA >= 2 (elevated mortality risk)")
    lab_deltas: List[LabDeltaMetric] = Field(default_factory=list, description="Serial laboratory kinetic delta analyses")
    symptom_progression_summary: str = Field(..., description="Structured narrative of symptom evolution and migration")
    trajectory_forecast: TrajectoryForecast = Field(..., description="Mathematical trajectory projection and ICU risk")
    chronological_event_stream: List[ChronologicalMilestoneEvent] = Field(default_factory=list, description="Merged chronological milestone timeline")
    executive_clinical_summary: str = Field(..., description="Concise hospitalist summary of patient's temporal state")
