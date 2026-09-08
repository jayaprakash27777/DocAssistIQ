import pytest
import uuid
from datetime import datetime
from app.services.safety_engine import safety_engine
from app.schemas.representation import ClinicalRepresentationResponse, RepresentationItem, PatientContext
from app.schemas.safety import SafetyDecision

def create_rep(symptoms_vals, negations_vals):
    return ClinicalRepresentationResponse(
        consultation_id=uuid.uuid4(),
        generated_at=datetime.utcnow(),
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(id=str(uuid.uuid4()), value=v) for v in symptoms_vals
        ],
        negations=[
            RepresentationItem(id=str(uuid.uuid4()), value=v) for v in negations_vals
        ]
    )

@pytest.mark.asyncio
async def test_red_flag_positive():
    rep = create_rep(["severe chest pain"], [])
    decision: SafetyDecision = await safety_engine.evaluate_clinical_representation(rep)
    assert decision.decision == "ABSTAIN"
    assert any(f.rule_id == "RF-001" for f in decision.flags)

@pytest.mark.asyncio
async def test_red_flag_negative():
    rep = create_rep(["mild chest discomfort"], [])
    decision: SafetyDecision = await safety_engine.evaluate_clinical_representation(rep)
    assert decision.decision == "ALLOW"
    assert len(decision.flags) == 0

@pytest.mark.asyncio
async def test_red_flag_contradictory():
    # Symptom says severe chest pain, but negation says "no chest pain"
    rep = create_rep(["severe chest pain"], ["chest pain"])
    decision: SafetyDecision = await safety_engine.evaluate_clinical_representation(rep)
    assert decision.decision == "ALLOW"
    assert len(decision.flags) == 0

@pytest.mark.asyncio
async def test_red_flag_borderline():
    # Missing severity
    rep = create_rep(["chest pain"], [])
    decision: SafetyDecision = await safety_engine.evaluate_clinical_representation(rep)
    assert decision.decision == "ALLOW"
    assert len(decision.flags) == 0

@pytest.mark.asyncio
async def test_red_flag_stroke():
    rep = create_rep(["facial droop", "sudden weakness"], [])
    decision: SafetyDecision = await safety_engine.evaluate_clinical_representation(rep)
    assert decision.decision == "ABSTAIN"
    assert any(f.rule_id == "RF-003" for f in decision.flags)
