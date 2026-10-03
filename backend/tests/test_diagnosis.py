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


@pytest.mark.asyncio
async def test_high_acuity_differential_accuracy() -> None:
    provider = BaselineDiagnosisProvider()

    # 1. Acute Myocardial Infarction / STEMI
    rep_mi = ClinicalRepresentationResponse(
        consultation_id="00000000-0000-0000-0000-000000000001",
        generated_at="2026-01-01T00:00:00Z",
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(value="crushing chest pain"),
            RepresentationItem(value="st elevation"),
            RepresentationItem(value="troponin elevation"),
            RepresentationItem(value="diaphoresis"),
        ],
    )
    res_mi = await provider.generate_differential(rep_mi)
    assert len(res_mi.top_candidates) > 0
    top_mi = res_mi.top_candidates[0]
    assert "Myocardial Infarction" in top_mi.disease or "STEMI" in top_mi.disease
    assert top_mi.score >= 0.85
    assert any("Aspirin" in m for m in top_mi.recommended_medications) or "Aspirin" in (top_mi.first_line_treatment or "")

    # 2. Status Epilepticus
    rep_se = ClinicalRepresentationResponse(
        consultation_id="00000000-0000-0000-0000-000000000002",
        generated_at="2026-01-01T00:00:00Z",
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(value="continuous seizures"),
            RepresentationItem(value="loss of consciousness"),
            RepresentationItem(value="tonic clonic activity"),
            RepresentationItem(value="unresponsiveness"),
        ],
    )
    res_se = await provider.generate_differential(rep_se)
    assert len(res_se.top_candidates) > 0
    top_se = res_se.top_candidates[0]
    assert top_se.disease == "Status Epilepticus"
    assert top_se.score >= 0.85
    assert any("Lorazepam" in m or "Levetiracetam" in m or "Fosphenytoin" in m for m in top_se.recommended_medications) or "Lorazepam" in (top_se.first_line_treatment or "")

    # 3. Bacterial Meningitis
    rep_men = ClinicalRepresentationResponse(
        consultation_id="00000000-0000-0000-0000-000000000003",
        generated_at="2026-01-01T00:00:00Z",
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(value="fever"),
            RepresentationItem(value="neck stiffness"),
            RepresentationItem(value="severe headache"),
            RepresentationItem(value="kernig sign"),
            RepresentationItem(value="photophobia"),
        ],
    )
    res_men = await provider.generate_differential(rep_men)
    assert len(res_men.top_candidates) > 0
    top_men = res_men.top_candidates[0]
    assert "Meningitis" in top_men.disease
    assert top_men.score >= 0.85
    assert any("Ceftriaxone" in m for m in top_men.recommended_medications) or "Ceftriaxone" in (top_men.first_line_treatment or "")

    # 4. Acute Upper Gastrointestinal Bleeding
    rep_gi = ClinicalRepresentationResponse(
        consultation_id="00000000-0000-0000-0000-000000000004",
        generated_at="2026-01-01T00:00:00Z",
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(value="hematemesis"),
            RepresentationItem(value="melena"),
            RepresentationItem(value="hypotension"),
            RepresentationItem(value="tachycardia"),
        ],
    )
    res_gi = await provider.generate_differential(rep_gi)
    assert len(res_gi.top_candidates) > 0
    top_gi = res_gi.top_candidates[0]
    assert "Gastrointestinal Bleeding" in top_gi.disease or "GI Bleed" in top_gi.disease
    assert top_gi.score >= 0.85
    assert any("Pantoprazole" in m or "Octreotide" in m for m in top_gi.recommended_medications) or "Pantoprazole" in (top_gi.first_line_treatment or "")

