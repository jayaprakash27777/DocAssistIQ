import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from app.infrastructure.database import get_session_factory

async def check():
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(text("""
            SELECT atttypmod FROM pg_attribute 
            WHERE attrelid = 'consultations'::regclass AND attname = 'clinical_representation_embedding';
        """))
        print('NEW DIMENSION atttypmod:', res.scalar())

asyncio.run(check())
