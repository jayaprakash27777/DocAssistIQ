import pytest
import uuid
from datetime import datetime
from app.services.diagnosis_provider import BaselineDiagnosisProvider
from app.schemas.representation import ClinicalRepresentationResponse, RepresentationItem, PatientContext
from app.schemas.diagnosis import DifferentialDiagnosisResponse

def create_rep(symptoms_vals, duration_vals, severity_vals):
    return ClinicalRepresentationResponse(
        consultation_id=uuid.uuid4(),
        generated_at=datetime.utcnow(),
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(id=str(uuid.uuid4()), value=v) for v in symptoms_vals
        ],
        negations=[],
        duration=[
            RepresentationItem(id=str(uuid.uuid4()), value=v) for v in duration_vals
        ],
        severity=[
            RepresentationItem(id=str(uuid.uuid4()), value=v) for v in severity_vals
        ]
    )

@pytest.mark.asyncio
async def test_uncertainty_insufficient_info():
    provider = BaselineDiagnosisProvider()
    rep = create_rep([], [], [])
    
    response = await provider.generate_differential(rep)
    assert response.status == "INSUFFICIENT_INFO"
    assert len(response.top_candidates) == 0
    assert any("symptom is required" in msg for msg in response.missing_critical_info)

@pytest.mark.asyncio
async def test_uncertainty_missing_severity_duration():
    provider = BaselineDiagnosisProvider()
    rep = create_rep(["cough"], [], [])
    
    response = await provider.generate_differential(rep)
    assert response.status == "SUCCESS"
    assert any("Duration" in msg for msg in response.missing_critical_info)
    assert any("Severity" in msg for msg in response.missing_critical_info)
    assert len(response.top_candidates) > 0
    # ensure uncertainty is High
    assert response.top_candidates[0].uncertainty == "High"

@pytest.mark.asyncio
async def test_uncertainty_success_with_info():
    provider = BaselineDiagnosisProvider()
    rep = create_rep(["cough", "fever"], ["3 days"], ["mild"])
    
    response = await provider.generate_differential(rep)
    assert response.status == "SUCCESS"
    assert len(response.missing_critical_info) == 0
    assert len(response.top_candidates) > 0
