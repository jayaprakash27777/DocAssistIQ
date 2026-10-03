"""DocAssistIQ — Automated Verification Tests for Clinical Safety Upgrades.

Tests:
1. Real-time PHI/PII de-identification (scrubbing names, phone, Aadhaar/SSN, DOB, addresses)
   while preserving 100% of clinical concepts (vitals, symptoms, medications, lab values).
2. Polypharmacy Anticholinergic Cognitive Burden (ACB) calculator based on Beers Criteria.
3. Renal clearance and nephrotoxic dosage warnings (eGFR / creatinine cutoffs).
4. Production security validation for JWT and Backend secrets.
"""

import pytest
from app.services.clinical_nlp import scrub_phi, deidentify_clinical_text
from app.services.polypharmacy_service import polypharmacy_simulator
from app.config import Settings, _DEV_SECRET_PLACEHOLDER, _DEV_JWT_SECRET_PLACEHOLDER
from pydantic import ValidationError


def test_phi_deidentification_real_case():
    """Verify that identifiable PII is scrubbed while clinical facts remain intact."""
    raw_text = (
        "Patient John Doe, 48M, DOB: 14/05/1976, mobile 9876543210, Aadhaar 1234 5678 9012, "
        "living at 142 Elm Street. Presents with high fever 102F, severe productive cough, "
        "and shortness of breath for 4 days. BP 130/85 mmHg, SpO2 91%. Prescribed Amoxicillin 500mg."
    )

    clean_text, redactions = scrub_phi(raw_text)

    # Identifiers must be redacted
    assert "John Doe" not in clean_text
    assert "9876543210" not in clean_text
    assert "1234 5678 9012" not in clean_text
    assert "142 Elm Street" not in clean_text
    assert "14/05/1976" not in clean_text

    # Clinical facts must remain 100% intact
    assert "48M" in clean_text
    assert "high fever 102F" in clean_text
    assert "productive cough" in clean_text
    assert "shortness of breath" in clean_text
    assert "BP 130/85 mmHg" in clean_text
    assert "SpO2 91%" in clean_text
    assert "Amoxicillin 500mg" in clean_text

    # Redactions metadata must record detected types
    redacted_types = {r["phi_type"] for r in redactions}
    assert "PATIENT_NAME" in redacted_types or "NAME" in clean_text
    assert "PHONE" in redacted_types
    assert "AADHAAR" in redacted_types
    assert "DOB" in redacted_types


def test_anticholinergic_cognitive_burden_calculation():
    """Test Beers Criteria ACB scoring on high-burden medication regimen."""
    # Amitriptyline is score 3 (high burden), Oxybutynin is score 3
    high_burden_regimen = ["Amitriptyline 25mg", "Oxybutynin 5mg", "Metoprolol 50mg"]
    acb = polypharmacy_simulator.calculate_anticholinergic_burden(high_burden_regimen)

    assert acb["total_score"] >= 6  # 3 + 3 = 6
    assert "High Risk" in acb["risk_category"]
    assert len(acb["contributing_medications"]) >= 2


def test_renal_safety_contraindication_metformin():
    """Test that Metformin triggers CRITICAL contraindication when eGFR < 30."""
    regimen = ["Metformin 1000mg", "Lisinopril 10mg"]
    alerts = polypharmacy_simulator.assess_renal_safety(regimen, egfr=24.0)

    metformin_alerts = [a for a in alerts if "Metformin" in a["title"]]
    assert len(metformin_alerts) >= 1
    assert metformin_alerts[0]["severity"] == "CRITICAL"
    assert "lactic acidosis" in metformin_alerts[0]["clinical_action"].lower()


def test_renal_safety_nsaid_warning():
    """Test that NSAIDs trigger AKI alert when eGFR < 30."""
    regimen = ["Ibuprofen 400mg", "Paracetamol 500mg"]
    alerts = polypharmacy_simulator.assess_renal_safety(regimen, egfr=22.0)

    nsaid_alerts = [a for a in alerts if "NSAID" in a["title"]]
    assert len(nsaid_alerts) >= 1
    assert nsaid_alerts[0]["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_polypharmacy_full_simulation_with_renal_and_acb():
    """Test end-to-end simulate() returns ACB, renal alerts, and safety notice."""
    response = await polypharmacy_simulator.simulate(
        proposed_meds=["Amitriptyline 25mg", "Ibuprofen 400mg"],
        current_meds=["Warfarin 5mg"],
        egfr=25.0
    )

    # Warfarin + Ibuprofen is CRITICAL DDI
    assert response.is_safe is False
    assert any(i.severity == "CRITICAL" for i in response.interactions)

    # ACB burden must be computed
    assert response.anticholinergic_burden is not None
    assert response.anticholinergic_burden["total_score"] >= 3

    # Renal alert for Ibuprofen in CKD must be present
    assert response.renal_alerts is not None
    assert any("NSAID" in a["title"] for a in response.renal_alerts)

    # Non-negotiable safety disclaimer must be present
    assert response.safety_disclaimer == "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"


def test_production_secret_validation_rejects_jwt_placeholder():
    """Verify that Settings fails fast in production if JWT_SECRET_KEY is unchanged."""
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            backend_secret_key="strong-production-backend-secret-key-12345",
            jwt_secret_key=_DEV_JWT_SECRET_PLACEHOLDER  # dev placeholder should be rejected
        )


def test_production_secret_validation_accepts_strong_secrets():
    """Verify that Settings succeeds when both keys are properly set in production."""
    settings = Settings(
        app_env="production",
        backend_secret_key="strong-production-backend-secret-key-12345",
        jwt_secret_key="strong-production-jwt-secret-key-67890"
    )
    assert settings.app_env == "production"


def test_critical_lab_panic_value_identification():
    """Verify that acute life-threatening laboratory panic values trigger stat alerts and protocols."""
    from app.services.lab_value_interpreter import lab_value_interpreter

    text = "Stat labs: serum potassium 6.8 mEq/L, lactate 4.5 mmol/L, platelets 15,000/uL, glucose 560 mg/dL"
    res = lab_value_interpreter.interpret(text)

    alerts = res.get("critical_panic_alerts", [])
    assert len(alerts) >= 3

    biomarkers = [a["biomarker"] for a in alerts]
    assert "Serum Potassium" in biomarkers
    assert "Serum Lactate" in biomarkers
    assert "Platelet Count" in biomarkers

    pot_alert = next(a for a in alerts if a["biomarker"] == "Serum Potassium")
    assert pot_alert["severity"] == "CRITICAL_PANIC_HIGH"
    assert "Calcium Gluconate" in pot_alert["immediate_bedside_protocol"]
    assert pot_alert["regulatory_watermark"] == "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"


def test_realtime_prediction_escalates_critical_panic_alert():
    """Verify that realtime prediction engine detects panic lab and triggers emergency alert."""
    from app.services.realtime_prediction_service import realtime_prediction_service

    note = "65yo male presenting with lethargy. Vitals stable. Labs show serum potassium 6.9 mEq/L."
    result = realtime_prediction_service.predict(symptoms=note)

    assert result["status"] == "SUCCESS"
    emergency = result.get("emergency_alert")
    assert emergency is not None
    assert emergency["is_emergency"] is True
    assert "CRITICAL" in emergency["condition"]
    assert "Calcium Gluconate" in emergency["immediate_action"]


def test_clinical_criteria_evaluator_named():
    """Verify that validated criteria calculations run with accurate clinical recommendations."""
    from app.services.clinical_criteria_evaluator import criteria_evaluator

    # 1. CHA2DS2-VASc
    af_res = criteria_evaluator.evaluate_named(
        name="cha2ds2_vasc",
        findings=["hypertension", "diabetes", "previous stroke"],
        labs={}
    )
    assert af_res["score"] >= 4
    assert af_res["risk_tier"] == "High"
    assert "anticoagulation" in af_res["recommendation"].lower()
    assert af_res["meets_criteria"] is True

    # 2. Wells PE
    pe_res = criteria_evaluator.evaluate_named(
        name="wells_pe",
        findings=["signs and symptoms of dvt", "pe is #1 diagnosis", "tachycardia", "hemoptysis"],
        labs={}
    )
    assert pe_res["score"] >= 6.0
    assert pe_res["risk_tier"] == "High"
    assert "ctpa" in pe_res["recommendation"].lower() or "cta" in pe_res["recommendation"].lower()

    # 3. CURB-65
    curb_res = criteria_evaluator.evaluate_named(
        name="curb65",
        findings=["confusion", "tachypnea", "age >= 65"],
        labs={"bun": {"value": 25.0}}
    )
    assert curb_res["score"] >= 3
    assert curb_res["risk_tier"] == "High"
    assert "hospital admission" in curb_res["recommendation"].lower() or "inpatient" in curb_res["recommendation"].lower()


def test_dynamic_model_switching_system_wide():
    """Verify that an administrator can switch the active AI model across the entire system."""
    from app.services.llm_service import llm_service
    from app.infrastructure.ai.factory import get_generation_provider

    original_model = llm_service.default_model

    try:
        # Switch to medical 8B
        llm_service.set_system_model("ii-medical:8b", fast_model="llama3.2:latest")
        assert llm_service.default_model == "ii-medical:8b"
        assert llm_service.fast_model == "llama3.2:latest"

        # Verify AI Factory provider reflects new model
        provider = get_generation_provider()
        assert provider.metadata.model_name == "ii-medical:8b"

        # Switch to Llama 3.1 8B
        llm_service.set_system_model("llama3.1:8b")
        assert llm_service.default_model == "llama3.1:8b"
        provider2 = get_generation_provider()
        assert provider2.metadata.model_name == "llama3.1:8b"
    finally:
        # Restore original model
        llm_service.set_system_model(original_model)


def test_circuit_breaker_force_offline_and_reset():
    """Verify that circuit breaker force offline mode and reset work deterministically."""
    from app.services.llm_service import _circuit_breaker

    try:
        _circuit_breaker.reset()
        assert _circuit_breaker.is_open is False
        assert _circuit_breaker.status["state"] == "CLOSED"

        # Force offline
        _circuit_breaker.set_force_open(True)
        assert _circuit_breaker.is_open is True
        assert _circuit_breaker.status["state"] == "FORCED_OFFLINE"
        assert _circuit_breaker.status["forced_offline"] is True

        # Reset back to healthy
        _circuit_breaker.reset()
        assert _circuit_breaker.is_open is False
        assert _circuit_breaker.status["state"] == "CLOSED"
        assert _circuit_breaker.status["forced_offline"] is False
    finally:
        _circuit_breaker.reset()


def test_admin_stats_schema_with_safety_alerts():
    """Verify that AdminStatsResponse correctly validates real-time safety alert counters."""
    from app.api.v1.endpoints.admin import AdminStatsResponse

    stats = AdminStatsResponse(
        total_users=42,
        total_doctors=30,
        total_admins=5,
        total_consultations=128,
        pending_verifications=3,
        total_safety_alerts=7,
        active_critical_alerts=1,
    )
    assert stats.total_consultations == 128
    assert stats.total_safety_alerts == 7
    assert stats.active_critical_alerts == 1


def test_admin_audit_logs_response_schema():
    """Verify AdminAuditLogsResponse schema and HIPAA compliance watermark."""
    import uuid
    from datetime import datetime, timezone
    from app.api.v1.endpoints.admin import AdminAuditLogsResponse, AuditLogItemResponse

    item = AuditLogItemResponse(
        id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        actor_id=uuid.uuid4(),
        actor_email="admin@hospital.org",
        actor_role="admin",
        action="admin.ai_model_switched",
        entity_type="ai_engine",
        severity="warning",
        diff='{"model": {"old": "llama3.1:8b", "new": "ii-medical:8b"}}',
    )
    res = AdminAuditLogsResponse(
        items=[item],
        total=1,
        critical_count=0,
        warning_count=1,
    )
    assert len(res.items) == 1
    assert res.items[0].action == "admin.ai_model_switched"
    assert res.items[0].severity == "warning"
    assert res.safety_watermark == "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"


@pytest.mark.asyncio
async def test_admin_user_update_self_guard():
    """Verify that administrators cannot demote or suspend themselves (safety guard)."""
    import uuid
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import HTTPException
    from app.api.v1.endpoints.admin import update_user, UpdateUserRequest
    from app.models.user import User

    admin_id = uuid.uuid4()
    admin_user = MagicMock(spec=User)
    admin_user.id = admin_id
    admin_user.email = "admin@example.com"
    admin_user.role = "admin"
    admin_user.is_active = True

    mock_db = AsyncMock()
    mock_db.get.return_value = admin_user

    # Attempting to suspend own account
    with pytest.raises(HTTPException) as exc_info:
        await update_user(
            user_id=admin_id,
            payload=UpdateUserRequest(is_active=False),
            db=mock_db,
            _current_admin=admin_user,
        )
    assert exc_info.value.status_code == 400
    assert "suspend their own account" in exc_info.value.detail

    # Attempting to change own role
    with pytest.raises(HTTPException) as exc_info2:
        await update_user(
            user_id=admin_id,
            payload=UpdateUserRequest(role="doctor"),
            db=mock_db,
            _current_admin=admin_user,
        )
    assert exc_info2.value.status_code == 400
    assert "cannot modify their own" in exc_info2.value.detail


@pytest.mark.asyncio
async def test_probe_ai_engine_when_circuit_breaker_open():
    """Verify that probe_ai_engine immediately returns fallback when circuit breaker is tripped."""
    from unittest.mock import MagicMock
    from app.api.v1.endpoints.admin import probe_ai_engine, ProbeAIResponse
    from app.services.llm_service import _circuit_breaker
    from app.models.user import User

    admin_user = MagicMock(spec=User)

    try:
        # Trip the circuit breaker
        _circuit_breaker.set_force_open(True)

        res = await probe_ai_engine(_current_admin=admin_user)
        assert isinstance(res, ProbeAIResponse)
        assert res.ok is False
        assert res.mode == "static_kb_fallback"
        assert "CIRCUIT BREAKER OPEN" in res.response
        assert res.latency_ms >= 0
    finally:
        _circuit_breaker.reset()


def test_probe_ai_response_schema():
    """Verify ProbeAIResponse schema validation with token speed calculations."""
    from app.api.v1.endpoints.admin import ProbeAIResponse

    probe = ProbeAIResponse(
        ok=True,
        model="ii-medical:8b",
        prompt="Clinical Probe Test",
        response="SYSTEM OPERATIONAL ii-medical:8b",
        latency_ms=124.5,
        tokens_evaluated=12,
        tokens_generated=8,
        eval_rate_tok_per_sec=38.4,
        mode="llm_active",
        timestamp="2026-09-30T16:00:00Z",
    )
    assert probe.ok is True
    assert probe.model == "ii-medical:8b"
    assert probe.latency_ms == 124.5
    assert probe.eval_rate_tok_per_sec == 38.4
    assert probe.safety_watermark == "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"



