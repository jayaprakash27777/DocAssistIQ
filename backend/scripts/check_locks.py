import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from sqlalchemy import text
from app.infrastructure.database import get_session_factory

async def check_locks():
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(text("""
            SELECT pid, state, query, age(clock_timestamp(), query_start) 
            FROM pg_stat_activity 
            WHERE datname = 'docassistiq' AND pid <> pg_backend_pid();
        """))
        for row in res.fetchall():
            print(row)

asyncio.run(check_locks())
