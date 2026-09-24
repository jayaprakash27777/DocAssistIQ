import pytest
from starlette.testclient import TestClient

from tests.test_consultations import _register_and_login, _create, _BASE_URL
from app.services.diagnosis_provider import BaselineDiagnosisProvider
from app.schemas.representation import ClinicalRepresentationResponse, PatientContext, RepresentationItem

@pytest.mark.asyncio
async def test_baseline_diagnosis_provider() -> None:
    # 1. Provide an exact match for Asthma
    rep1 = ClinicalRepresentationResponse(
        consultation_id="00000000-0000-0000-0000-000000000000",
        generated_at="2026-01-01T00:00:00Z",
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(value="cough"),
            RepresentationItem(value="shortness of breath"),
            RepresentationItem(value="wheezing"),
            RepresentationItem(value="chest tightness")
        ]
    )
    
    provider = BaselineDiagnosisProvider()
    res1 = await provider.generate_differential(rep1)
    
    assert res1.top_candidates[0].disease == "Asthma"
    assert res1.top_candidates[0].score == 1.0
    assert "wheezing" in res1.top_candidates[0].supporting_findings
    assert len(res1.top_candidates[0].recommended_investigations) > 0 or len(res1.top_candidates[0].immediate_tests) > 0
    assert len(res1.top_candidates[0].recommended_medications) > 0
    assert res1.top_candidates[0].first_line_treatment is not None

    # 2. Provide a contradiction for Asthma
    rep2 = ClinicalRepresentationResponse(
        consultation_id="00000000-0000-0000-0000-000000000000",
        generated_at="2026-01-01T00:00:00Z",
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(value="cough"),
            RepresentationItem(value="shortness of breath"),
        ],
        negations=[
            RepresentationItem(value="wheezing")  # contradiction
        ]
    )
    res2 = await provider.generate_differential(rep2)
    asthma_candidate = next((c for c in res2.top_candidates if c.disease == "Asthma"), None)
    
    assert asthma_candidate is not None
    # Score should be penalized: (2 / 4) - (1 * 0.2) = 0.5 - 0.2 = 0.3
    assert asthma_candidate.score == 0.3
    assert "wheezing" in asthma_candidate.contradicting_information


@pytest.mark.integration
def test_get_differential_endpoint(test_client: TestClient) -> None:
    token = _register_and_login(test_client)
    created = _create(test_client, token)
    assert created.status_code == 201
    consultation_id = created.json()["id"]

    r = test_client.get(
        f"{_BASE_URL}/consultations/{consultation_id}/differential",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["provider_metadata"]["provider"] in ["BaselineDiagnosisProvider", "OllamaDiagnosisProvider"]
    
    # Since it's an empty consultation, top candidates should be empty
    assert len(body["top_candidates"]) == 0
