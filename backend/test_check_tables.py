import asyncio
from app.infrastructure.database import get_session_factory
from sqlalchemy import text

async def check_tables():
    session_factory = get_session_factory()
    async with session_factory() as db:
        res = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [r[0] for r in res.fetchall()]
        print("Tables in DB:", sorted(tables))
        
        # Check consultations count
        res_c = await db.execute(text("SELECT count(*) FROM consultations"))
        print("Consultations count:", res_c.scalar())

        # Check patient_profiles count
        res_p = await db.execute(text("SELECT count(*) FROM patient_profiles"))
        print("Patient profiles count:", res_p.scalar())

        # Check patient_sessions count
        res_s = await db.execute(text("SELECT count(*) FROM patient_sessions"))
        print("Patient sessions count:", res_s.scalar())

if __name__ == "__main__":
    asyncio.run(check_tables())
