import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text, select
from app.infrastructure.database import get_engine, get_session_factory, Base
from app.models.user import User
from app.models.doctor import Doctor
from app.services.auth_service import hash_password
import uuid

async def setup():
    engine = get_engine()
    factory = get_session_factory()
    
    # 1. Create all missing tables if any
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        await conn.run_sync(Base.metadata.create_all)
        print("Base.metadata.create_all executed.")

    async with factory() as session:
        # 2. Check and alter column vector dimension to 768
        try:
            await session.execute(text("ALTER TABLE consultations ALTER COLUMN clinical_representation_embedding TYPE vector(768);"))
            await session.commit()
            print("consultations.clinical_representation_embedding ensured as vector(768).")
        except Exception as e:
            print(f"Altering column: {e}")
            await session.rollback()

        # 3. Ensure default tenant exists
        from app.models.tenant import Tenant
        tenant = await session.scalar(select(Tenant).limit(1))
        if not tenant:
            tenant = Tenant(
                name="DocAssistIQ Academic Medical Center",
                slug="docassistiq-amc",
                status="active",
                plan="enterprise",
                contact_email="admin@hospital.org"
            )
            session.add(tenant)
            await session.flush()
            print(f"Created default tenant {tenant.name} ({tenant.id})")
        else:
            print(f"Default tenant exists: {tenant.name} ({tenant.id})")

        # 4. Ensure test doctor exists
        doctor_user = await session.scalar(select(User).where(User.email == "dr.smith@hospital.org"))
        if not doctor_user:
            doctor_user = User(
                email="dr.smith@hospital.org",
                password_hash=hash_password("DoctorSecure2026!"),
                full_name="Dr Smith",
                role="doctor",
                is_active=True,
            )
            session.add(doctor_user)
            await session.flush()
            print(f"Created Dr. Smith user with ID {doctor_user.id}")
            
            doctor_profile = Doctor(
                user_id=doctor_user.id,
                tenant_id=tenant.id,
                specialty="Cardiology",
                credential_reference="MD-2026-9999",
                credential_body="General Medical Council",
                verification_status="verified"
            )
            session.add(doctor_profile)
            await session.commit()
            print("Created Dr. Smith doctor profile.")
        else:
            doctor_user.full_name = "Dr Smith"
            doctor_profile = await session.scalar(select(Doctor).where(Doctor.user_id == doctor_user.id))
            if doctor_profile and not doctor_profile.tenant_id:
                doctor_profile.tenant_id = tenant.id
            await session.commit()
            print("Dr Smith full_name and tenant updated.")

    print("DATABASE READY AND VERIFIED!")

if __name__ == "__main__":
    asyncio.run(setup())
