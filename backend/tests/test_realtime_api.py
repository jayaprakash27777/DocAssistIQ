"""DocAssistIQ — Integration test for Real-Time Prediction API."""

import pytest
from starlette.testclient import TestClient
from tests.test_consultations import _register_and_login, _create, _BASE_URL

@pytest.mark.integration
def test_predict_realtime_endpoint(test_client: TestClient) -> None:

    token = _register_and_login(test_client)
    
    # 1. Test POST /api/v1/consultations/predict-realtime
    payload = {
        "symptoms": "periumbilical pain migrating to right lower quadrant, nausea, vomiting, McBurney point tenderness",
    }
    r = test_client.post(
        f"{_BASE_URL}/consultations/predict-realtime",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.json()
    data = r.json()
    assert data["status"] == "SUCCESS"
    assert data["latency_ms"] < 100.0  # Real-time requirement
    assert len(data["top_candidates"]) > 0
    assert data["top_candidates"][0]["disease"] == "Acute Appendicitis"
    assert "%" in data["top_candidates"][0]["display_score"]
    assert data["top_candidates"][0]["triage"] == "EMERGENT"
    assert len(data["top_candidates"][0]["immediate_tests"]) > 0

    # 2. Test Emergency Alert for Acute Aortic Dissection
    payload_emergency = {
        "symptoms": "sudden severe tearing chest pain radiating to back between shoulder blades, bp discrepancy between arms",
    }
    r_em = test_client.post(
        f"{_BASE_URL}/consultations/predict-realtime",
        json=payload_emergency,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_em.status_code == 200
    data_em = r_em.json()
    assert data_em["emergency_alert"] is not None
    assert data_em["emergency_alert"]["is_emergency"] is True
    assert "Aortic Dissection" in data_em["emergency_alert"]["condition"]

    # 3. Test Open Domain Disease (Wilson's Disease)
    payload_od = {
        "symptoms": "kayser-fleischer rings, copper accumulation, asterixis, jaundice, tremor",
    }
    r_od = test_client.post(
        f"{_BASE_URL}/consultations/predict-realtime",
        json=payload_od,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_od.status_code == 200
    data_od = r_od.json()
    assert len(data_od["top_candidates"]) > 0
    assert "Wilson" in data_od["top_candidates"][0]["disease"]

    # 4. Test High-Impact Physician Clinical Decision Support (CDS) features
    payload_chest_pain = {
        "symptoms": "52 yo male with crushing substernal chest pain, diaphoresis, shortness of breath, radiating to left arm",
    }
    r_cds = test_client.post(
        f"{_BASE_URL}/consultations/predict-realtime",
        json=payload_chest_pain,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_cds.status_code == 200
    data_cds = r_cds.json()
    assert "must_not_miss_candidates" in data_cds
    assert data_cds["must_not_miss_candidates"] is not None
    assert len(data_cds["must_not_miss_candidates"]) > 0
    assert any("Aortic Dissection" in c["disease"] or "Coronary" in c["disease"] for c in data_cds["must_not_miss_candidates"])

    assert "bedside_clarifying_questions" in data_cds
    assert data_cds["bedside_clarifying_questions"] is not None
    assert len(data_cds["bedside_clarifying_questions"]) > 0

    assert "comparison_matrix" in data_cds
    assert data_cds["comparison_matrix"] is not None
    assert len(data_cds["comparison_matrix"]) > 0

    assert "clinical_mdm_summary" in data_cds
    assert data_cds["clinical_mdm_summary"] is not None
    assert "CLINICAL ASSESSMENT & MEDICAL DECISION MAKING" in data_cds["clinical_mdm_summary"]

    # 5. Test Live Consultation Session Integration with Unstructured Doctor Notes
    r_create = test_client.post(
        f"{_BASE_URL}/consultations",
        json={
            "input_text": "Patient is a 48 yo male presenting with acute crushing chest pain, diaphoresis, left arm radiation, BP 140/85, HR 92. Denies trauma or cough.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_create.status_code == 201
    cons_id = r_create.json()["id"]

    # Test GET /consultations/{id}/predict-realtime using DB input_text without ?symptoms=
    r_cons_realtime = test_client.get(
        f"{_BASE_URL}/consultations/{cons_id}/predict-realtime",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_cons_realtime.status_code == 200
    data_cons_rt = r_cons_realtime.json()
    assert data_cons_rt["status"] == "SUCCESS"
    assert len(data_cons_rt["top_candidates"]) > 0
    assert any("Coronary" in c["disease"] or "Myocardial" in c["disease"] or "Angina" in c["disease"] for c in data_cons_rt["top_candidates"])

    # Test GET /consultations/{id}/differential using DB input_text without ?symptoms=
    r_cons_diff = test_client.get(
        f"{_BASE_URL}/consultations/{cons_id}/differential",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_cons_diff.status_code == 200
    data_cons_diff = r_cons_diff.json()
    assert data_cons_diff["status"] == "SUCCESS"
    assert len(data_cons_diff["top_candidates"]) > 0

