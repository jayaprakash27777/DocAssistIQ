import asyncio
import sys
import uuid
sys.path.insert(0, r"c:\Users\User\Downloads\DocAssistIQ\backend")
from app.infrastructure.database import get_session_factory, atomic
from app.models.consultation import Consultation
from app.models.doctor import Doctor
from app.models.user import User
from app.models.clinical import ClinicalNote
from sqlalchemy import select

async def main():
    session_factory = get_session_factory()
    async with session_factory() as db:
        cid = uuid.UUID("98608ffb-5089-44c6-992e-2d2c6ef11e00")
        c = await db.scalar(select(Consultation).where(Consultation.id == cid))
        if not c:
            print("Consultation not found")
            return
        print(f"Consultation: id={c.id}, doctor_id={c.doctor_id}")
        doc = await db.scalar(select(Doctor).where(Doctor.id == c.doctor_id))
        print(f"Doctor: {doc}")
        if doc:
            user = await db.scalar(select(User).where(User.id == doc.user_id))
            print(f"User: full_name={user.full_name if user else None}, email={user.email if user else None}")
        
        note = await db.scalar(select(ClinicalNote).where(ClinicalNote.consultation_id == cid))
        if note:
            body = note.body or {}
            hdr = body.get("patient_encounter_header", {})
            print(f"Current Clinical Note Header: {hdr}")

if __name__ == "__main__":
    asyncio.run(main())
