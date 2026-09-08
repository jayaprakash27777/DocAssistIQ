import pytest
import uuid
from datetime import datetime
from app.services.safety_engine import safety_engine
from app.schemas.diagnosis import DifferentialDiagnosisItem
from app.schemas.representation import ClinicalRepresentationResponse, RepresentationItem
from app.schemas.safety import SafetyDecision

from app.models.knowledge import Disease

@pytest.mark.asyncio
async def test_safety_engine_contradiction(db_session):
    async with db_session.begin():
        disease = Disease(id=uuid.uuid4(), name="Hypertension", code="I10")
        db_session.add(disease)
        
    # Mock data
    item = DifferentialDiagnosisItem(
        disease="Hypertension",
        score=0.8,
        supporting_findings=[],
        missing_expected_findings=[],
        contradicting_information=["negated finding 1", "negated finding 2", "negated finding 3"],
        uncertainty="Low",
        explanation_reference="Test"
    )
    
    rep = ClinicalRepresentationResponse(
        consultation_id=uuid.uuid4(),
        generated_at=datetime.utcnow(),
        patient_context={"age": 45, "gender": "male"},
        symptoms=[],
        negations=[],
        chronic_conditions=[],
        medications=[],
        allergies=[],
        vitals=[],
        investigations=[],
        report_findings=[]
    )
    async with db_session.begin():
        decision: SafetyDecision = await safety_engine.evaluate_differential_item(db_session, item, rep)
    
    assert decision.decision in ["WARN", "ABSTAIN"]
    assert any(f.category == "CONTRADICTION" for f in decision.flags)

@pytest.mark.asyncio
async def test_safety_engine_red_flag(db_session):
    async with db_session.begin():
        disease = Disease(id=uuid.uuid4(), name="Gastroenteritis", code="A09")
        db_session.add(disease)
        
    item = DifferentialDiagnosisItem(
        disease="Gastroenteritis",
        score=0.8,
        supporting_findings=["nausea"],
        missing_expected_findings=[],
        contradicting_information=[],
        uncertainty="Low",
        explanation_reference="Test"
    )
    
    rep = ClinicalRepresentationResponse(
        consultation_id=uuid.uuid4(),
        generated_at=datetime.utcnow(),
        patient_context={"age": 45, "gender": "male"},
        symptoms=[
            RepresentationItem(id=str(uuid.uuid4()), concept=None, value="severe chest pain", confidence=1.0)
        ],
        negations=[],
        chronic_conditions=[],
        medications=[],
        allergies=[],
        vitals=[],
        investigations=[],
        report_findings=[]
    )
    async with db_session.begin():
        decision: SafetyDecision = await safety_engine.evaluate_differential_item(db_session, item, rep)
    
    assert decision.decision == "ABSTAIN"
    assert any(f.category == "RED_FLAG" for f in decision.flags)
