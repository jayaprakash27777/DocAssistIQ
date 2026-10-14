import asyncio
import sys
import uuid

sys.path.insert(0, r"c:\Users\User\Downloads\DocAssistIQ\backend")

from app.infrastructure.database import get_session_factory
from app.models.consultation import Consultation
from app.models.clinical import ClinicalNote
from app.services.note_generator import note_generator_service
from sqlalchemy import select


async def main():
    session_factory = get_session_factory()
    async with session_factory() as db:
        cid = uuid.UUID("98608ffb-5089-44c6-992e-2d2c6ef11e00")
        c = await db.scalar(select(Consultation).where(Consultation.id == cid))
        if not c:
            print("Consultation not found")
            return
        
        print(f"Reprocessing note for consultation: {c.id}, doctor_id: {c.doctor_id}")
        note = await note_generator_service.draft_note_from_findings(
            db=db,
            consultation_id=c.id,
            doctor_id=c.doctor_id,
        )
        print("Note drafted successfully!")
        body = note.body or {}
        header = body.get("patient_encounter_header", {})
        print("\n=== GENERATED PATIENT ENCOUNTER HEADER ===")
        for k, v in header.items():
            print(f"  {k}: {v}")
        
        formatted_md = body.get("_meta", {}).get("formatted_ehr_text", "")
        print("\n=== TOP OF FORMATTED EHR TEXT ===")
        print("\n".join(formatted_md.splitlines()[:15]))


if __name__ == "__main__":
    asyncio.run(main())
