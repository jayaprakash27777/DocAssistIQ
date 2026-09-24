import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from sqlalchemy import text
from app.infrastructure.database import get_session_factory

async def check_all():
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(text("""
            SELECT c.relname, a.attname, a.atttypmod 
            FROM pg_attribute a 
            JOIN pg_class c ON a.attrelid = c.oid 
            JOIN pg_type t ON a.atttypid = t.oid 
            WHERE t.typname = 'vector';
        """))
        for row in res.fetchall():
            print(f"Table: {row[0]}, Column: {row[1]}, Dimension: {row[2]}")

asyncio.run(check_all())
