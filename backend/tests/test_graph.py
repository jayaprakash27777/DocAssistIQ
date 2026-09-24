import uuid
import pytest
from starlette.testclient import TestClient

from app.models.knowledge import (
    Disease, Symptom, Medicine,
    DiseaseSymptom, DiseaseMedicine, MedicineContraindication
)
from tests.test_consultations import _register_and_login, _auth

@pytest.mark.asyncio
async def test_get_disease_graph_unit(unit_session):
    from app.services.graph_service import get_disease_knowledge_graph
    from app.models.knowledge import Disease, Symptom, Medicine, DiseaseSymptom, DiseaseMedicine
    from fastapi import HTTPException

    await unit_session.begin()

    # 1. Non-existent returns 404

    with pytest.raises(HTTPException) as exc_info:
        await get_disease_knowledge_graph(unit_session, uuid.uuid4())
    assert exc_info.value.status_code == 404

    # 2. Create Disease, Symptom, Medicine and relationships
    disease = Disease(
        code="ICD10:J45",
        name="Bronchial Asthma",
        category="Respiratory",
        description="Chronic inflammatory disorder of the airways",
        status="verified"
    )
    symptom = Symptom(
        code="SNOMED:267036007",
        name="Dyspnea / Shortness of breath",
        description="Difficulty breathing",
        status="verified"
    )

    medicine = Medicine(
        code="RxNorm:161",
        name="Albuterol sulfate",
        drug_class="Beta-2 Agonist",
        status="verified"
    )

    unit_session.add_all([disease, symptom, medicine])
    await unit_session.flush()

    ds = DiseaseSymptom(
        disease_id=disease.id,
        symptom_id=symptom.id,
        frequency="common",
        specificity=0.85
    )

    dm = DiseaseMedicine(
        disease_id=disease.id,
        medicine_id=medicine.id,
        treatment_role="first_line"
    )
    unit_session.add_all([ds, dm])
    await unit_session.flush()

    # 3. Retrieve graph
    graph = await get_disease_knowledge_graph(unit_session, disease.id)
    assert graph.disease_id == disease.id
    node_types = {n.node_type for n in graph.nodes}
    assert "disease" in node_types
    assert "symptom" in node_types
    assert "medicine" in node_types
    
    edge_rels = {e.relationship for e in graph.edges}
    assert "has_symptom" in edge_rels
    assert "treated_by" in edge_rels


@pytest.mark.integration
def test_get_disease_graph_not_found(test_client: TestClient):
    token = _register_and_login(test_client)
    fake_id = str(uuid.uuid4())
    
    response = test_client.get(
        f"/api/v1/knowledge/diseases/{fake_id}/graph",
        headers=_auth(token)
    )
    
    assert response.status_code == 404

