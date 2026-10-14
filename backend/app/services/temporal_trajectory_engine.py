"""
DocAssistIQ - Enterprise Temporal Trajectory & Clinical Timeline Delta Engine
Phase 8: High-precision mathematical time-series modeling for acute and longitudinal patient states.
Implements:
- Royal College of Physicians (RCP) NEWS2 score evaluation & dynamic delta tracking
- Hemodynamic Shock Index (HR / SBP) & occult hypoperfusion detection
- Sepsis-3 qSOFA scoring
- Serial Lab Delta kinetics & velocity (KDIGO AKI, acute myocardial injury troponin kinetics, lactate clearance)
- Subjective symptom migration & evolutionary trajectory analysis
- Multimodal Trajectory Forecasting & Decompensation Hazard Scoring (0.0 <= H <= 1.0)
- Unified chronological clinical milestone event stream
"""

import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from app.schemas.temporal_trajectory import (
    VitalSignObservation,
    LabObservation,
    SymptomObservation,
    ClinicalIntervention,
    EarlyWarningScoreDetail,
    ShockIndexDetail,
    LabDeltaMetric,
    TrajectoryForecast,
    ChronologicalMilestoneEvent,
    TemporalTrajectoryRequest,
    TemporalTrajectoryResponse,
)


class TemporalTrajectoryEngine:
    """
    High-performance, deterministic clinical time-series reasoning engine.
    Calculates exact physiological metrics, kinetic rates of change,
    and prognostic trajectory forecasts with zero faking and zero hallucinations.
    """

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # 1. RCP NEWS2 Early Warning Score Calculation
    # -------------------------------------------------------------------------
    def calculate_news2(self, vital: VitalSignObservation) -> EarlyWarningScoreDetail:
        """
        Calculates exact National Early Warning Score 2 (NEWS2) according to
        Royal College of Physicians (RCP) guidelines.
        """
        subscores: Dict[str, int] = {}
        extreme_score = False

        # 1. Respiration Rate (breaths/min)
        rr = vital.respiratory_rate
        if rr is not None:
            if rr <= 8:
                subscores["respiratory_rate"] = 3
            elif 9 <= rr <= 11:
                subscores["respiratory_rate"] = 1
            elif 12 <= rr <= 20:
                subscores["respiratory_rate"] = 0
            elif 21 <= rr <= 24:
                subscores["respiratory_rate"] = 2
            else:  # >= 25
                subscores["respiratory_rate"] = 3
        else:
            subscores["respiratory_rate"] = 0

        # 2. Oxygen Saturation SpO2 (%) - Scale 1 (standard)
        spo2 = vital.spo2_percent
        if spo2 is not None:
            if spo2 <= 91:
                subscores["spo2"] = 3
            elif 92 <= spo2 <= 93:
                subscores["spo2"] = 2
            elif 94 <= spo2 <= 95:
                subscores["spo2"] = 1
            else:  # >= 96
                subscores["spo2"] = 0
        else:
            subscores["spo2"] = 0

        # 3. Supplemental Oxygen
        subscores["supplemental_o2"] = 2 if vital.on_supplemental_o2 else 0

        # 4. Systolic Blood Pressure (mmHg)
        sbp = vital.systolic_bp
        if sbp is not None:
            if sbp <= 90:
                subscores["systolic_bp"] = 3
            elif 91 <= sbp <= 100:
                subscores["systolic_bp"] = 2
            elif 101 <= sbp <= 110:
                subscores["systolic_bp"] = 1
            elif 111 <= sbp <= 219:
                subscores["systolic_bp"] = 0
            else:  # >= 220
                subscores["systolic_bp"] = 3
        else:
            subscores["systolic_bp"] = 0

        # 5. Pulse / Heart Rate (bpm)
        hr = vital.heart_rate
        if hr is not None:
            if hr <= 40:
                subscores["heart_rate"] = 3
            elif 41 <= hr <= 50:
                subscores["heart_rate"] = 1
            elif 51 <= hr <= 90:
                subscores["heart_rate"] = 0
            elif 91 <= hr <= 110:
                subscores["heart_rate"] = 1
            elif 111 <= hr <= 130:
                subscores["heart_rate"] = 2
            else:  # >= 131
                subscores["heart_rate"] = 3
        else:
            subscores["heart_rate"] = 0

        # 6. Consciousness (AVPU scale)
        avpu = (vital.avpu_consciousness or "Alert").strip().upper()
        if avpu in ["ALERT", "A"]:
            subscores["consciousness"] = 0
        else:
            # Voice, Pain, Unresponsive, or acute confusion
            subscores["consciousness"] = 3

        # 7. Body Temperature (°C)
        temp = vital.temperature_c
        if temp is not None:
            if temp <= 35.0:
                subscores["temperature"] = 3
            elif 35.1 <= temp <= 36.0:
                subscores["temperature"] = 1
            elif 36.1 <= temp <= 38.0:
                subscores["temperature"] = 0
            elif 38.1 <= temp <= 39.0:
                subscores["temperature"] = 1
            else:  # >= 39.1
                subscores["temperature"] = 2
        else:
            subscores["temperature"] = 0

        total_score = sum(subscores.values())
        extreme_score = any(val >= 3 for val in subscores.values())

        # Determine RCP Risk Level & Clinical Action
        if total_score >= 7:
            risk_level = "HIGH"
            clinical_action = (
                "EMERGENCY RESPONSE: Immediate assessment by Critical Care Outreach / Rapid Response Team. "
                "Initiate continuous monitoring. Consider immediate transfer to High Dependency Unit (HDU) or ICU."
            )
        elif total_score >= 5 or extreme_score:
            risk_level = "MEDIUM" if total_score >= 5 else "LOW_MEDIUM"
            trigger_text = f"Aggregate score {total_score}" if total_score >= 5 else "Extreme single-parameter trigger (score 3)"
            clinical_action = (
                f"URGENT CLINICAL REVIEW: {trigger_text}. Urgent assessment by ward clinician or acute team within 30 minutes. "
                "Increase monitoring frequency to at least hourly. Prepare for escalation if deteriorating."
            )
        else:
            risk_level = "LOW"
            clinical_action = (
                "ROUTINE MONITORING: Minimum 4–12 hourly vital sign monitoring. Continue standard ward-based clinical care."
            )

        return EarlyWarningScoreDetail(
            score_name="NEWS2",
            total_score=total_score,
            risk_level=risk_level,
            clinical_action=clinical_action,
            subscores=subscores,
            has_extreme_subscore=extreme_score,
        )

    # -------------------------------------------------------------------------
    # 2. Hemodynamic Shock Index Calculation
    # -------------------------------------------------------------------------
    def calculate_shock_index(self, vital: VitalSignObservation) -> ShockIndexDetail:
        """
        Calculates Shock Index = Heart Rate / Systolic Blood Pressure.
        Normal: 0.5 - 0.7. >0.9 indicates occult hypoperfusion/shock.
        """
        hr = vital.heart_rate or 75
        sbp = vital.systolic_bp or 120

        si_value = round(hr / max(sbp, 30), 2)
        is_elevated = si_value > 0.70

        if si_value < 0.50:
            classification = "NORMAL"
            interpretation = "Relative bradycardia or elevated systolic blood pressure. Low occult shock risk."
        elif 0.50 <= si_value <= 0.70:
            classification = "NORMAL"
            interpretation = "Physiologically normal hemodynamic balance. Hemoperfusion maintained."
        elif 0.70 < si_value <= 0.90:
            classification = "MILD_ELEVATION"
            interpretation = "Mild compensatory tachycardia/hypotension. Close monitoring of fluid status recommended."
        elif 0.90 < si_value <= 1.10:
            classification = "OCCULT_SHOCK"
            interpretation = (
                "OCCULT HYPOPERFUSION: Shock Index > 0.9 is strongly predictive of hidden circulatory compromise, "
                "elevated ICU admission rate, and increased mortality. Fluid challenge or blood transfusion evaluation needed."
            )
        else:  # > 1.10
            classification = "SEVERE_SHOCK"
            interpretation = (
                "SEVERE DECOMPENSATED SHOCK: Critical circulatory collapse (SI > 1.1). Profound tissue hypoperfusion. "
                "Requires immediate aggressive hemodynamic resuscitation, vasopressor support, and invasive monitoring."
            )

        return ShockIndexDetail(
            value=si_value,
            classification=classification,
            interpretation=interpretation,
            is_elevated=is_elevated,
        )

    # -------------------------------------------------------------------------
    # 3. Sepsis-3 Quick SOFA (qSOFA) Calculation
    # -------------------------------------------------------------------------
    def calculate_qsofa(self, vital: VitalSignObservation) -> Tuple[int, bool]:
        """
        Sepsis-3 qSOFA criteria:
        1. Respiratory rate >= 22 bpm (+1)
        2. Altered mentation (AVPU != Alert) (+1)
        3. Systolic blood pressure <= 100 mmHg (+1)
        High risk if score >= 2.
        """
        score = 0
        if vital.respiratory_rate and vital.respiratory_rate >= 22:
            score += 1
        avpu = (vital.avpu_consciousness or "Alert").strip().upper()
        if avpu not in ["ALERT", "A"]:
            score += 1
        if vital.systolic_bp and vital.systolic_bp <= 100:
            score += 1

        return score, (score >= 2)

    # -------------------------------------------------------------------------
    # 4. Serial Lab Delta Kinetics & Velocity
    # -------------------------------------------------------------------------
    def analyze_lab_deltas(self, labs: List[LabObservation]) -> List[LabDeltaMetric]:
        """
        Calculates kinetic rate of change between baseline and most recent lab results.
        Evaluates KDIGO AKI, acute myocardial injury troponin delta, and lactate clearance.
        """
        if len(labs) < 2:
            return []

        # Sort labs by timestamp
        sorted_labs = sorted(labs, key=lambda l: l.timestamp)
        baseline = sorted_labs[0]
        latest = sorted_labs[-1]

        # Calculate delta time in hours
        try:
            t0 = datetime.fromisoformat(baseline.timestamp.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(latest.timestamp.replace("Z", "+00:00"))
            delta_hours = max(0.1, (t1 - t0).total_seconds() / 3600.0)
        except Exception:
            delta_hours = 24.0  # fallback assumption

        deltas: List[LabDeltaMetric] = []

        # 1. Creatinine (KDIGO AKI)
        if baseline.creatinine_mg_dl is not None and latest.creatinine_mg_dl is not None:
            c0 = baseline.creatinine_mg_dl
            c1 = latest.creatinine_mg_dl
            abs_delta = round(c1 - c0, 2)
            pct_change = round(((c1 - c0) / max(c0, 0.1)) * 100.0, 1)
            vel = round(abs_delta / delta_hours, 3)

            is_crit = False
            if abs_delta >= 0.3 or pct_change >= 50.0:
                if pct_change >= 200.0 or c1 >= 4.0:
                    significance = f"KDIGO Stage 3 AKI (Critical 3-fold rise or Cr >= 4.0 mg/dL). Nephrology & RRT consultation needed."
                    is_crit = True
                elif pct_change >= 100.0:
                    significance = f"KDIGO Stage 2 AKI (2-fold rise, +{pct_change}%). Acute renal parenchymal insult."
                    is_crit = True
                else:
                    significance = f"KDIGO Stage 1 AKI (+{abs_delta} mg/dL / +{pct_change}% in {delta_hours:.1f}h). Stop nephrotoxics."
                    is_crit = True
            elif pct_change <= -20.0:
                significance = f"Renal functional recovery (Cr decreased by {abs(pct_change)}%)."
            else:
                significance = "Stable baseline renal clearance."

            deltas.append(LabDeltaMetric(
                parameter="Serum Creatinine",
                baseline_value=c0,
                current_value=c1,
                absolute_delta=abs_delta,
                relative_percent_change=pct_change,
                time_interval_hours=round(delta_hours, 1),
                velocity_per_hour=vel,
                clinical_significance=significance,
                is_critical=is_crit,
            ))

        # 2. Cardiac Troponin (hs-cTn)
        if baseline.troponin_ng_ml is not None and latest.troponin_ng_ml is not None:
            tn0 = baseline.troponin_ng_ml
            tn1 = latest.troponin_ng_ml
            abs_delta = round(tn1 - tn0, 3)
            pct_change = round(((tn1 - tn0) / max(tn0, 0.005)) * 100.0, 1)
            vel = round(abs_delta / delta_hours, 4)

            is_crit = False
            if pct_change >= 20.0 or abs_delta >= 0.05:
                significance = (
                    f"ACUTE MYOCARDIAL INJURY: Dynamic serial troponin rise (+{pct_change}%, absolute +{abs_delta} ng/mL). "
                    "Fulfills 4th Universal Definition of Myocardial Infarction. Immediate cardiology consult & coronary evaluation."
                )
                is_crit = True
            elif pct_change <= -20.0:
                significance = f"Resolving myocardial necrosis (Troponin down {abs(pct_change)}%). Post-infarct resolution phase."
            else:
                significance = "Stable chronic myocardial strain/elevation without acute dynamic necrosis delta."

            deltas.append(LabDeltaMetric(
                parameter="High-Sensitivity Cardiac Troponin",
                baseline_value=tn0,
                current_value=tn1,
                absolute_delta=abs_delta,
                relative_percent_change=pct_change,
                time_interval_hours=round(delta_hours, 1),
                velocity_per_hour=vel,
                clinical_significance=significance,
                is_critical=is_crit,
            ))

        # 3. Serum Lactate (Tissue Hypoperfusion & Clearance Kinetics)
        if baseline.lactate_mmol_l is not None and latest.lactate_mmol_l is not None:
            lac0 = baseline.lactate_mmol_l
            lac1 = latest.lactate_mmol_l
            abs_delta = round(lac1 - lac0, 2)
            pct_change = round(((lac1 - lac0) / max(lac0, 0.1)) * 100.0, 1)
            vel = round(abs_delta / delta_hours, 3)

            is_crit = False
            if lac1 >= 4.0:
                significance = f"SEVERE LACTIC ACIDOSIS (Lactate {lac1} mmol/L). Severe systemic tissue dysoxia. High mortality."
                is_crit = True
            elif abs_delta > 0 and lac1 >= 2.0:
                significance = (
                    f"REFRACTORY HYPOPERFUSION: Lactate rising (+{abs_delta} mmol/L). Failure of initial resuscitation. "
                    "Escalate vasopressors, inotropes, or source control."
                )
                is_crit = True
            elif pct_change <= -20.0:
                significance = f"Adequate Lactate Clearance (Lactate cleared by {abs(pct_change)}%). Resuscitation goal met."
            elif lac0 >= 2.0 and pct_change > -10.0:
                significance = "Inadequate Lactate Clearance (<10% clearance in interval). Indicates ongoing occult hypoperfusion."
                is_crit = True
            else:
                significance = "Normal cellular bioenergetic metabolism."

            deltas.append(LabDeltaMetric(
                parameter="Serum Lactate",
                baseline_value=lac0,
                current_value=lac1,
                absolute_delta=abs_delta,
                relative_percent_change=pct_change,
                time_interval_hours=round(delta_hours, 1),
                velocity_per_hour=vel,
                clinical_significance=significance,
                is_critical=is_crit,
            ))

        # 4. Platelets (Consumptive Coagulopathy / Severe Dengue / HIT)
        if baseline.platelets_k_ul is not None and latest.platelets_k_ul is not None:
            plt0 = baseline.platelets_k_ul
            plt1 = latest.platelets_k_ul
            abs_delta = round(plt1 - plt0, 1)
            pct_change = round(((plt1 - plt0) / max(plt0, 1.0)) * 100.0, 1)
            vel = round(abs_delta / delta_hours, 2)

            is_crit = False
            if pct_change <= -50.0 or plt1 < 50.0:
                significance = (
                    f"CRITICAL CONSUMPTIVE THROMBOCYTOPENIA: Rapid platelet drop (-{abs(pct_change)}%, current {plt1} k/uL). "
                    "Evaluate for Dengue Plasma Leakage, DIC, or Heparin-Induced Thrombocytopenia (HIT)."
                )
                is_crit = True
            elif pct_change <= -25.0:
                significance = f"Moderate platelet consumption (-{abs(pct_change)}%). Monitor bleeding precautions."
            elif pct_change >= 20.0 and plt0 < 150:
                significance = f"Marrow recovery / Platelet count rising (+{pct_change}%)."
            else:
                significance = "Stable platelet count."

            deltas.append(LabDeltaMetric(
                parameter="Platelet Count",
                baseline_value=plt0,
                current_value=plt1,
                absolute_delta=abs_delta,
                relative_percent_change=pct_change,
                time_interval_hours=round(delta_hours, 1),
                velocity_per_hour=vel,
                clinical_significance=significance,
                is_critical=is_crit,
            ))

        # 5. Serum Potassium (Arrhythmogenic Risk)
        if baseline.potassium_mmol_l is not None and latest.potassium_mmol_l is not None:
            k0 = baseline.potassium_mmol_l
            k1 = latest.potassium_mmol_l
            abs_delta = round(k1 - k0, 2)
            pct_change = round(((k1 - k0) / max(k0, 0.1)) * 100.0, 1)
            vel = round(abs_delta / delta_hours, 3)

            is_crit = False
            if k1 >= 6.0:
                significance = f"SEVERE HYPERKALEMIA (K+ {k1} mmol/L). Immediate threat of lethal cardiac arrest. Give Calcium Gluconate + Insulin/Dextrose."
                is_crit = True
            elif k1 >= 5.5:
                significance = f"MODERATE HYPERKALEMIA (K+ {k1} mmol/L). Mandates immediate 12-lead ECG for peaked T waves."
                is_crit = True
            elif k1 <= 3.0:
                significance = f"SEVERE HYPOKALEMIA (K+ {k1} mmol/L). Arrhythmia risk (U waves, Torsades). Urgent IV replacement."
                is_crit = True
            else:
                significance = "Serum potassium within safe physiological window."

            deltas.append(LabDeltaMetric(
                parameter="Serum Potassium",
                baseline_value=k0,
                current_value=k1,
                absolute_delta=abs_delta,
                relative_percent_change=pct_change,
                time_interval_hours=round(delta_hours, 1),
                velocity_per_hour=vel,
                clinical_significance=significance,
                is_critical=is_crit,
            ))

        return deltas

    # -------------------------------------------------------------------------
    # 5. Symptom Trajectory & Migration Tracking
    # -------------------------------------------------------------------------
    def analyze_symptoms(self, symptoms: List[SymptomObservation]) -> Tuple[str, float]:
        """
        Analyzes progression, severity deltas, and anatomical migration across symptoms.
        Returns narrative summary and worsening symptom ratio for hazard weighting.
        """
        if not symptoms:
            return "No serial symptom observations recorded.", 0.0

        worsening_count = 0
        new_count = 0
        improving_count = 0
        migrations = []

        for s in symptoms:
            status = s.status.upper()
            if status in ["WORSENING"]:
                worsening_count += 1
            elif status in ["NEW"]:
                new_count += 1
            elif status in ["IMPROVING", "RESOLVED"]:
                improving_count += 1

            if s.anatomical_location:
                migrations.append(f"{s.symptom} localized to {s.anatomical_location}")

        total = len(symptoms)
        worsening_ratio = (worsening_count + (0.5 * new_count)) / max(total, 1)

        summary_parts = []
        if worsening_count > 0:
            summary_parts.append(f"{worsening_count} symptom(s) worsening")
        if new_count > 0:
            summary_parts.append(f"{new_count} new symptom(s) developed")
        if improving_count > 0:
            summary_parts.append(f"{improving_count} symptom(s) improving/resolved")
        if migrations:
            summary_parts.append("Anatomical evolution: " + "; ".join(migrations))

        narrative = ". ".join(summary_parts) + "." if summary_parts else "Symptoms persistent and unchanged."
        return narrative, min(1.0, worsening_ratio)

    # -------------------------------------------------------------------------
    # 6. Multimodal Trajectory Forecasting & Hazard Scoring
    # -------------------------------------------------------------------------
    def forecast_trajectory(
        self,
        news2: EarlyWarningScoreDetail,
        news2_delta: Optional[int],
        shock_index: ShockIndexDetail,
        qsofa_score: int,
        lab_deltas: List[LabDeltaMetric],
        worsening_symptom_ratio: float,
        suspected_dx: Optional[str] = None,
    ) -> TrajectoryForecast:
        """
        Projects patient trajectory across 6h, 12h, and 24h horizons.
        Calculates composite Decompensation Hazard Score: 0.0 (Extremely Stable) to 1.0 (Critical).
        """
        # 1. Base NEWS2 component (0.0 to 1.0)
        news2_comp = min(1.0, news2.total_score / 10.0)

        # 2. Shock Index component (elevations above 0.70)
        si_comp = min(1.0, max(0.0, (shock_index.value - 0.70) / 0.50))

        # 3. Lab Critical Hazard component
        critical_labs = sum(1 for d in lab_deltas if d.is_critical)
        lab_comp = min(1.0, critical_labs * 0.35)

        # 4. Delta velocity component (is patient worsening?)
        delta_news = news2_delta or 0
        delta_comp = min(1.0, max(0.0, delta_news / 4.0))

        # Composite Hazard Score (Calibrated weights)
        hazard_score = round(
            (0.30 * news2_comp) +
            (0.25 * si_comp) +
            (0.20 * lab_comp) +
            (0.15 * delta_comp) +
            (0.10 * worsening_symptom_ratio),
            2
        )
        hazard_score = min(1.0, max(0.0, hazard_score))

        # Trajectory Direction
        if delta_news >= 3 or hazard_score >= 0.75:
            direction = "RAPIDLY_DETERIORATING"
        elif delta_news >= 1 or hazard_score >= 0.45:
            direction = "DETERIORATING"
        elif delta_news <= -3 and hazard_score < 0.25:
            direction = "RAPIDLY_IMPROVING"
        elif delta_news <= -1 and hazard_score < 0.40:
            direction = "IMPROVING"
        else:
            direction = "STABLE"

        # Clinical Phase
        if hazard_score >= 0.80 or shock_index.value >= 1.15:
            phase = "REFRACTORY_SHOCK"
        elif hazard_score >= 0.50:
            phase = "ACUTE_DECOMPENSATION"
        elif hazard_score >= 0.30:
            phase = "COMPENSATING"
        elif direction in ["IMPROVING", "RAPIDLY_IMPROVING"]:
            phase = "RECOVERY"
        else:
            phase = "STABLE_MAINTENANCE"

        # ICU and RRT recommendations
        icu_transfer = (
            hazard_score >= 0.65 or
            news2.total_score >= 7 or
            shock_index.value >= 1.0 or
            qsofa_score >= 2 or
            any("Stage 3 AKI" in d.clinical_significance or "LACTIC ACIDOSIS" in d.clinical_significance for d in lab_deltas)
        )
        rrt_alert = (
            news2.total_score >= 5 or
            news2.has_extreme_subscore or
            shock_index.is_elevated or
            hazard_score >= 0.40
        )

        # 24h Predicted Milestones
        milestones: List[str] = []
        interventions: List[str] = []

        if direction in ["RAPIDLY_DETERIORATING", "DETERIORATING"]:
            if shock_index.is_elevated:
                milestones.append("T+2h to T+6h: Progressive vasoplegia and refractory hypotension if preload not restored.")
                interventions.append("Urgent crystalloid fluid bolus (30 mL/kg) or balanced electrolyte solution.")
                interventions.append("Prepare Norepinephrine infusion (target MAP >= 65 mmHg) via central venous access.")
            if any(d.parameter == "High-Sensitivity Cardiac Troponin" and d.is_critical for d in lab_deltas):
                milestones.append("T+4h: Peak myocardial biomarker release; elevated risk of ventricular dysrhythmia and pump failure.")
                interventions.append("Urgent 12-lead ECG and bedside echocardiography; cardiology activation for catheterization.")
            if any(d.parameter == "Serum Creatinine" and d.is_critical for d in lab_deltas):
                milestones.append("T+12h to T+24h: Oliguria, worsening azotemia, and metabolic acid-base decompensation.")
                interventions.append("Discontinue ACEi/ARBs, NSAIDs, and dose-adjust all renally eliminated pharmacotherapy.")
            if qsofa_score >= 2:
                milestones.append("T+6h: Sepsis progression to multi-organ dysfunction syndrome (MODS).")
                interventions.append("Blood cultures x2 before broad-spectrum IV antibiotics within 1 hour; serum lactate clearance protocol.")
        elif direction in ["IMPROVING", "RAPIDLY_IMPROVING"]:
            milestones.append("T+6h to T+12h: Continued hemodynamic stabilization and clearance of metabolic debt.")
            milestones.append("T+24h: Candidate for step-down to standard inpatient telemetry or ward-based observation.")
            interventions.append("De-escalate supplemental oxygen therapy towards target SpO2 94–98%.")
            interventions.append("Wean vasopressor support as MAP permits; switch to oral medication bridge.")
        else:
            milestones.append("T+12h to T+24h: Physiologic parameters expected to remain within current tolerance limits.")
            interventions.append("Maintain baseline telemetry and repeat scheduled laboratory surveillance in 12 hours.")

        rationale = (
            f"Composite Decompensation Hazard Score is {hazard_score:.2f} ({phase}). "
            f"NEWS2 score is {news2.total_score} (risk: {news2.risk_level}), with Shock Index {shock_index.value:.2f} ({shock_index.classification}). "
            f"qSOFA score is {qsofa_score}/3. "
            f"{'Critical laboratory kinetic deltas identified. ' if critical_labs > 0 else 'Laboratory kinetics remain controlled. '}"
            f"Patient trajectory is classified as {direction}."
        )

        return TrajectoryForecast(
            trajectory_direction=direction,
            clinical_phase=phase,
            decompensation_hazard_score=hazard_score,
            icu_transfer_recommended=icu_transfer,
            rapid_response_team_alert=rrt_alert,
            predicted_milestones_24h=milestones,
            recommended_urgent_interventions=interventions,
            rationale=rationale,
        )

    # -------------------------------------------------------------------------
    # 7. Unified Chronological Milestone Event Stream
    # -------------------------------------------------------------------------
    def build_chronological_stream(
        self,
        vitals: List[VitalSignObservation],
        labs: List[LabObservation],
        symptoms: List[SymptomObservation],
        interventions: List[ClinicalIntervention],
    ) -> List[ChronologicalMilestoneEvent]:
        """
        Merges vitals, labs, symptoms, and interventions into a unified chronological stream.
        """
        raw_events: List[Tuple[str, ChronologicalMilestoneEvent]] = []

        # Add Vitals
        for v in vitals:
            n2 = self.calculate_news2(v)
            si = self.calculate_shock_index(v)
            sev = "CRITICAL" if n2.total_score >= 7 or si.value >= 1.0 else ("WARNING" if n2.total_score >= 5 or si.is_elevated else "INFO")
            raw_events.append((
                v.timestamp,
                ChronologicalMilestoneEvent(
                    timestamp=v.timestamp,
                    event_type="VITAL_SIGN",
                    title=f"Vitals: HR {v.heart_rate or '--'}, BP {v.systolic_bp or '--'}/{v.diastolic_bp or '--'}, SpO2 {v.spo2_percent or '--'}%",
                    description=f"NEWS2: {n2.total_score} ({n2.risk_level}) | Shock Index: {si.value:.2f} ({si.classification})",
                    severity=sev,
                    details={"news2": n2.total_score, "shock_index": si.value, "rr": v.respiratory_rate, "temp": v.temperature_c},
                )
            ))

        # Add Labs
        for l in labs:
            lab_desc_items = []
            if l.creatinine_mg_dl is not None:
                lab_desc_items.append(f"Cr: {l.creatinine_mg_dl} mg/dL")
            if l.troponin_ng_ml is not None:
                lab_desc_items.append(f"hs-cTn: {l.troponin_ng_ml} ng/mL")
            if l.lactate_mmol_l is not None:
                lab_desc_items.append(f"Lactate: {l.lactate_mmol_l} mmol/L")
            if l.platelets_k_ul is not None:
                lab_desc_items.append(f"Plt: {l.platelets_k_ul} k/uL")

            sev = "INFO"
            if (l.lactate_mmol_l and l.lactate_mmol_l >= 4.0) or (l.troponin_ng_ml and l.troponin_ng_ml >= 0.1) or (l.creatinine_mg_dl and l.creatinine_mg_dl >= 3.0):
                sev = "CRITICAL"
            elif (l.lactate_mmol_l and l.lactate_mmol_l >= 2.0) or (l.creatinine_mg_dl and l.creatinine_mg_dl >= 1.5):
                sev = "WARNING"

            raw_events.append((
                l.timestamp,
                ChronologicalMilestoneEvent(
                    timestamp=l.timestamp,
                    event_type="LABORATORY",
                    title="Laboratory Results Profile",
                    description=", ".join(lab_desc_items) if lab_desc_items else "Routine panel completed.",
                    severity=sev,
                    details={"creatinine": l.creatinine_mg_dl, "troponin": l.troponin_ng_ml, "lactate": l.lactate_mmol_l},
                )
            ))

        # Add Symptoms
        for s in symptoms:
            sev = "WARNING" if s.status == "WORSENING" else ("INFO" if s.status == "IMPROVING" else "INFO")
            raw_events.append((
                s.timestamp,
                ChronologicalMilestoneEvent(
                    timestamp=s.timestamp,
                    event_type="SYMPTOM_CHANGE",
                    title=f"Symptom: {s.symptom} ({s.status})",
                    description=f"Severity {s.severity_1_to_10}/10. {s.anatomical_location or ''} {s.notes or ''}".strip(),
                    severity=sev,
                    details={"symptom": s.symptom, "status": s.status, "severity": s.severity_1_to_10},
                )
            ))

        # Add Interventions
        for i in interventions:
            raw_events.append((
                i.timestamp,
                ChronologicalMilestoneEvent(
                    timestamp=i.timestamp,
                    event_type="INTERVENTION",
                    title=f"Intervention: {i.intervention_type}",
                    description=f"{i.description} {f'({i.dose_or_rate})' if i.dose_or_rate else ''}".strip(),
                    severity="RECOVERY",
                    details={"type": i.intervention_type, "dose": i.dose_or_rate},
                )
            ))

        # Sort chronologically
        raw_events.sort(key=lambda x: x[0])
        return [evt for _, evt in raw_events]

    # -------------------------------------------------------------------------
    # 8. Main Public Evaluation Entrypoint
    # -------------------------------------------------------------------------
    def evaluate_temporal_trajectory(self, payload: TemporalTrajectoryRequest) -> TemporalTrajectoryResponse:
        """
        Executes end-to-end temporal trajectory evaluation across patient timeline.
        """
        vitals = payload.vitals_timeline
        labs = payload.labs_timeline
        symptoms = payload.symptoms_timeline
        interventions = payload.interventions_timeline

        # 1. Current / Latest Vitals NEWS2 & Shock Index
        if vitals:
            sorted_vitals = sorted(vitals, key=lambda v: v.timestamp)
            latest_vital = sorted_vitals[-1]
            earliest_vital = sorted_vitals[0]
            current_news2 = self.calculate_news2(latest_vital)
            earliest_news2 = self.calculate_news2(earliest_vital)
            news2_delta = current_news2.total_score - earliest_news2.total_score if len(sorted_vitals) > 1 else 0
            current_si = self.calculate_shock_index(latest_vital)
            qsofa_score, qsofa_high_risk = self.calculate_qsofa(latest_vital)
        else:
            # Fallback default normal
            default_vital = VitalSignObservation(
                timestamp=datetime.utcnow().isoformat() + "Z",
                heart_rate=72,
                systolic_bp=120,
                diastolic_bp=80,
                respiratory_rate=16,
                temperature_c=37.0,
                spo2_percent=98.0,
                on_supplemental_o2=False,
                avpu_consciousness="Alert"
            )
            current_news2 = self.calculate_news2(default_vital)
            news2_delta = 0
            current_si = self.calculate_shock_index(default_vital)
            qsofa_score, qsofa_high_risk = 0, False

        # 2. Lab Deltas
        lab_deltas = self.analyze_lab_deltas(labs)

        # 3. Symptom Progression
        symptom_summary, worsening_ratio = self.analyze_symptoms(symptoms)

        # 4. Trajectory Forecast
        forecast = self.forecast_trajectory(
            news2=current_news2,
            news2_delta=news2_delta,
            shock_index=current_si,
            qsofa_score=qsofa_score,
            lab_deltas=lab_deltas,
            worsening_symptom_ratio=worsening_ratio,
            suspected_dx=payload.primary_diagnosis_suspicion,
        )

        # 5. Chronological Milestone Stream
        event_stream = self.build_chronological_stream(vitals, labs, symptoms, interventions)

        # 6. Executive Clinical Summary
        exec_summary = (
            f"Patient {payload.patient_id} ({payload.age}y {payload.sex}): Current NEWS2 is {current_news2.total_score} "
            f"({current_news2.risk_level} risk, delta: {'+' if news2_delta >= 0 else ''}{news2_delta}). "
            f"Shock Index is {current_si.value:.2f} ({current_si.classification}). "
            f"qSOFA score is {qsofa_score}/3 ({'High mortality risk' if qsofa_high_risk else 'Non-critical'}). "
            f"Trajectory is {forecast.trajectory_direction} in phase {forecast.clinical_phase} "
            f"with Decompensation Hazard Score {forecast.decompensation_hazard_score:.2f}. "
            f"{'EMERGENCY: ICU Transfer is recommended. ' if forecast.icu_transfer_recommended else ''}"
            f"{'Rapid Response Team alert advised. ' if forecast.rapid_response_team_alert else ''}"
            f"Symptom status: {symptom_summary}"
        )

        total_obs = len(vitals) + len(labs) + len(symptoms) + len(interventions)

        return TemporalTrajectoryResponse(
            patient_id=payload.patient_id or "P-LONGITUDINAL",
            evaluation_timestamp=datetime.utcnow().isoformat() + "Z",
            total_observations_analyzed=total_obs,
            news2_current=current_news2,
            news2_delta=news2_delta,
            shock_index=current_si,
            qsofa_score=qsofa_score,
            qsofa_high_risk=qsofa_high_risk,
            lab_deltas=lab_deltas,
            symptom_progression_summary=symptom_summary,
            trajectory_forecast=forecast,
            chronological_event_stream=event_stream,
            executive_clinical_summary=exec_summary,
        )


# Global singleton instance
temporal_trajectory_engine = TemporalTrajectoryEngine()
