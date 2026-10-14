import asyncio
import sys
import uuid

sys.path.insert(0, r"c:\Users\User\Downloads\DocAssistIQ\backend")

from app.infrastructure.database import get_session_factory
from app.models.consultation import Consultation
from app.models.patient import PatientSession
from app.models.patient_profile import PatientProfile
from app.models.clinical import ClinicalNote
from app.services.note_generator import _extract_patient_header, extract_patient_name
from sqlalchemy import select


async def main():
    session_factory = get_session_factory()
    async with session_factory() as db:
        cid = uuid.UUID("98608ffb-5089-44c6-992e-2d2c6ef11e00")
        c = await db.scalar(select(Consultation).where(Consultation.id == cid))
        print("=== CONSULTATION ===")
        print(f"id: {c.id}")
        print(f"doctor_id: {c.doctor_id}")
        print(f"patient_session_id: {c.patient_session_id}")
        print(f"input_text: {c.input_text!r}")
        
        if c.patient_session_id:
            sess = await db.scalar(select(PatientSession).where(PatientSession.id == c.patient_session_id))
            print(f"sess: {sess}, profile_id={sess.patient_profile_id if sess else None}")
            if sess and sess.patient_profile_id:
                prof = await db.scalar(select(PatientProfile).where(PatientProfile.id == sess.patient_profile_id))
                print(f"prof: patient_ref={prof.patient_ref if prof else None}")
                if prof:
                    print(f"prof dict: {prof.__dict__}")

        pname = extract_patient_name(c.input_text or "")
        print(f"extract_patient_name(input_text): {pname!r}")

        hdr = await _extract_patient_header(
            consultation=c,
            raw_text=c.input_text or "",
            db=db,
            doctor_id=c.doctor_id,
            chief_complaint="Bleeding",
        )
        print("=== FRESH _extract_patient_header RESULT ===")
        for k, v in hdr.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
