import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.infrastructure.database import get_session_factory
from app.models.consultation import Consultation
from app.models.doctor import Doctor
from app.services.case_retrieval import find_similar_cases, get_or_create_consultation_embedding
from sqlalchemy import select

async def test_case_retrieval():
    factory = get_session_factory()
    async with factory() as session:
        # Fetch an existing doctor
        doctor = (await session.execute(select(Doctor))).scalars().first()
        if not doctor:
            print("No doctor found, skipping test")
            return
        
        # Create a test consultation
        cons = Consultation(
            doctor_id=doctor.id,
            input_text="Patient presents with acute chest pain radiating to left arm and diaphoresis.",
            status="created",
            tenant_id=doctor.tenant_id
        )
        session.add(cons)
        await session.commit()
        await session.refresh(cons)
        print(f"Created test consultation ID: {cons.id}")

        # Test embedding creation
        vec = await get_or_create_consultation_embedding(session, cons)
        print(f"Embedding generated and committed! Length: {len(vec)}, is list: {isinstance(vec, list)}")

        # Test find_similar_cases
        similar = await find_similar_cases(session, cons.id, limit=5)
        print(f"Similar cases search succeeded! Found: {len(similar)} cases")

asyncio.run(test_case_retrieval())
