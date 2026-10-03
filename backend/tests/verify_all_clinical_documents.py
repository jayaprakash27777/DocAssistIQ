import asyncio
import uuid
import sys
from app.infrastructure.database import get_session_factory
from app.services.clinical_document_service import clinical_document_service

async def test_all_7():
    session_factory = get_session_factory()
    cid = uuid.UUID("a994e376-9e25-4759-922f-191c3b6710ea")
    doc_types = [
        "discharge_summary",
        "medical_certificate",
        "care_plan",
        "patient_profile",
        "encounter_timeline",
        "referral_letter",
        "lab_order",
    ]
    async with session_factory() as db:
        for dt in doc_types:
            doc_data = await clinical_document_service.build_document_data(db, cid, dt)
            pdf = clinical_document_service.generate_pdf(doc_data)
            docx_out = clinical_document_service.generate_docx(doc_data)
            sig = doc_data["digital_signature"]
            title = doc_data["title"]
            print(f"[{dt}] Title: {title} | Sections: {len(doc_data['sections'])} | PDF: {len(pdf)} bytes | DOCX: {len(docx_out)} bytes | Sig: {sig['verification_code']}")
            assert len(pdf) > 2500, f"PDF too small for {dt}"
            assert len(docx_out) > 20000, f"DOCX too small for {dt}"
            assert sig["verification_code"].startswith("DOCASSIST-SIG-"), f"Invalid sig for {dt}"

if __name__ == "__main__":
    asyncio.run(test_all_7())
