import hashlib
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import Investigation
from app.models.embedding import EmbeddingRecord
from app.infrastructure.ai.factory import get_embedding_provider

log = structlog.get_logger(__name__)

MOCK_LAB_TESTS = [
    {
        "code": "LOINC-17856-6",
        "name": "HbA1c (Hemoglobin A1c)",
        "description": "Measures the amount of blood sugar (glucose) attached to hemoglobin. Used to diagnose and monitor Type 2 Diabetes and prediabetes.",
        "rationale": "High priority test to evaluate long-term glycemic control over the past 2-3 months.",
        "limitations": "May be inaccurate in patients with hemoglobinopathies or recent blood loss."
    },
    {
        "code": "LOINC-58410-2",
        "name": "Complete Blood Count (CBC) with differential",
        "description": "Evaluates overall health and detects a wide range of disorders, including anemia, infection, and leukemia.",
        "rationale": "Crucial baseline investigation to assess anemia, immune response, and overall hematologic status.",
        "limitations": "Non-specific; requires clinical correlation and often follow-up tests."
    },
    {
        "code": "LOINC-14927-8",
        "name": "Dengue NS1 Antigen",
        "description": "Detects the non-structural protein 1 (NS1) of the dengue virus. Used for early detection of dengue fever.",
        "rationale": "High priority in suspected acute dengue fever cases within the first 1-5 days of symptom onset.",
        "limitations": "Sensitivity decreases after day 5 of illness."
    },
    {
        "code": "LOINC-2093-3",
        "name": "Cholesterol Panel (Lipid Profile)",
        "description": "Measures total cholesterol, LDL, HDL, and triglycerides. Used to determine the risk of heart disease.",
        "rationale": "Routine screening for cardiovascular risk assessment.",
        "limitations": "Typically requires 9-12 hours of fasting for accurate triglyceride measurement."
    },
    {
        "code": "LOINC-24321-2",
        "name": "Basic Metabolic Panel (BMP)",
        "description": "Measures glucose, calcium, and electrolytes, as well as kidney function (BUN and creatinine).",
        "rationale": "Essential for evaluating electrolyte balance and renal function.",
        "limitations": "Does not assess liver function."
    },
    {
        "code": "LOINC-1751-7",
        "name": "Albumin",
        "description": "Measures the amount of albumin in the clear liquid portion of the blood. Used to screen for liver or kidney disease.",
        "rationale": "Helps evaluate nutritional status and liver/kidney disease.",
        "limitations": "Can be decreased in acute inflammation or infection."
    },
    {
        "code": "LOINC-2345-7",
        "name": "Glucose, fasting",
        "description": "Measures the amount of glucose in the blood after an 8-12 hour fast.",
        "rationale": "Used to diagnose and monitor diabetes.",
        "limitations": "Requires strict fasting."
    }
]

class MedlinePlusLabTestsIngester:
    """
    Ingests MedlinePlus / LOINC lab tests.
    Creates Investigation knowledge records and embedding vectors for RAG.
    """

    async def ingest_lab_tests_stub(self, db: AsyncSession) -> int:
        """
        Ingests a predefined set of critical lab tests for demonstration and testing.
        In a production system, this would parse a MedlinePlus XML/JSON API or LOINC CSV.
        """
        provider = get_embedding_provider()
        ingested_count = 0

        for test_data in MOCK_LAB_TESTS:
            code_str = test_data["code"]
            
            # 1. Check if already ingested
            existing = await db.scalar(select(Investigation).where(Investigation.code == code_str))
            if existing:
                continue

            # 2. Create Investigation Record
            inv = Investigation(
                code=code_str,
                name=test_data["name"],
                description=test_data["description"],
                status="APPROVED",
                is_ai_generated=False,
                credibility_tier="primary"
            )
            db.add(inv)
            await db.flush()

            # 3. Create RAG Embedding Context
            embed_text = f"Investigation Test: {test_data['name']}\nCode: {code_str}\nDescription: {test_data['description']}\nClinical Rationale: {test_data['rationale']}\nLimitations: {test_data['limitations']}"
            
            try:
                vector = await provider.embed(embed_text)
                
                emb = EmbeddingRecord(
                    source_record_type="investigation",
                    source_record_id=str(inv.id),
                    embedding_model=provider.metadata.model_name,
                    model_version="1.0",
                    dimensions=len(vector),
                    embedding=vector,
                    content_hash=hashlib.sha256(embed_text.encode("utf-8")).hexdigest()
                )
                db.add(emb)
                ingested_count += 1
                log.info("ingested_lab_test", name=test_data["name"], code=code_str)
            except Exception as e:
                log.error("failed_to_embed_lab_test", error=str(e), code=code_str)

        await db.commit()
        return ingested_count

lab_tests_ingester = MedlinePlusLabTestsIngester()
