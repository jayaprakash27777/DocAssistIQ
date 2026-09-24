import asyncio
import uuid
from sqlalchemy import select
from app.infrastructure.database import get_session_factory
from app.models.user import User
from app.models.doctor import Doctor
from app.models.tenant import Tenant
from app.services.auth_service import hash_password

async def seed_users():
    session_maker = get_session_factory()
    accounts = [
        {
            'email': 'admin@docassistiq.com',
            'full_name': 'System Administrator',
            'role': 'admin',
            'password': 'AdminSecure2026!'
        },
        {
            'email': 'admin@hospital.org',
            'full_name': 'Hospital Administrator',
            'role': 'admin',
            'password': 'AdminSecure2026!'
        },
        {
            'email': 'dr.smith@hospital.org',
            'full_name': 'Dr. John Smith',
            'role': 'doctor',
            'password': 'DoctorSecure2026!'
        },
        {
            'email': 'e2e_test5@docassistiq.com',
            'full_name': 'Dr. E2E Tester',
            'role': 'doctor',
            'password': 'DoctorSecure2026!'
        }
    ]

    async with session_maker() as db:
        for acc in accounts:
            existing = await db.scalar(select(User).where(User.email == acc['email']))
            if existing:
                print(f"User {acc['email']} exists. Updating password hash...")
                existing.password_hash = hash_password(acc['password'])
                existing.is_active = True
                existing.role = acc['role']
                existing.full_name = acc['full_name']
                user_id = existing.id
            else:
                print(f"Creating user {acc['email']}...")
                new_user = User(
                    id=uuid.uuid4(),
                    email=acc['email'],
                    password_hash=hash_password(acc['password']),
                    full_name=acc['full_name'],
                    role=acc['role'],
                    is_active=True
                )
                db.add(new_user)
                await db.flush()
                user_id = new_user.id

            if acc['role'] == 'doctor':
                existing_doc = await db.scalar(select(Doctor).where(Doctor.user_id == user_id))
                if not existing_doc:
                    t_slug = f"practice-{uuid.uuid4().hex[:8]}"
                    t_name = f"{acc['full_name']} Practice"
                    tenant = Tenant(name=t_name, slug=t_slug)
                    db.add(tenant)
                    await db.flush()
                    doc = Doctor(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        tenant_id=tenant.id,
                        specialty='Cardiology',
                        credential_reference='MED-12345678',
                        credential_body='Medical Board',
                        verification_status='verified'
                    )
                    db.add(doc)
                    print(f"Created verified doctor profile for {acc['email']}")
                else:
                    existing_doc.verification_status = 'verified'
                    existing_doc.specialty = 'Cardiology'
                    print(f"Doctor profile for {acc['email']} marked verified")

        await db.commit()
        print("All demo and admin users successfully seeded and committed!")

if __name__ == "__main__":
    asyncio.run(seed_users())
