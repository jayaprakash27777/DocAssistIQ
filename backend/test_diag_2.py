import asyncio
import sys
import uuid
import os

# Add backend dir to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.diagnosis_provider import OllamaDiagnosisProvider
from app.schemas.representation import ClinicalRepresentationResponse, PatientContext, RepresentationItem

async def mock_retrieve(db, query, top_k):
    return ""

async def main():
    import app.services.diagnosis_provider
    app.services.diagnosis_provider.retrieve_medical_context = mock_retrieve

    provider = OllamaDiagnosisProvider()
    rep = ClinicalRepresentationResponse(
        consultation_id=uuid.uuid4(),
        generated_at="2026-09-14T00:00:00Z",
        patient_context=PatientContext(),
        symptoms=[
            RepresentationItem(value="headache", concept="symptom", status="pending", provenances=[]),
            RepresentationItem(value="fever", concept="symptom", status="pending", provenances=[])
        ],
        duration=[],
        severity=[],
        negations=[],
        history=[],
        medications=[],
        allergies=[],
        vitals=[],
        investigations=[],
        report_findings=[]
    )
    
    try:
        print("Running generate_differential...")
        res = await provider.generate_differential(None, rep)
        print("Status:", res.status)
        print("Candidates count:", len(res.top_candidates))
        for c in res.top_candidates:
            print(f"- {c.disease} (Score: {c.score}, Uncertainty: {c.uncertainty})")
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
