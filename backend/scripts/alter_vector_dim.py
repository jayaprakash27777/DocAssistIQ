import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from app.infrastructure.database import get_session_factory

async def update_dim():
    factory = get_session_factory()
    async with factory() as session:
        # Terminate any stale idle transactions holding locks on consultations
        await session.execute(text("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = 'docassistiq' 
              AND pid <> pg_backend_pid() 
              AND state = 'idle in transaction';
        """))
        await session.commit()
        
        await session.execute(text("ALTER TABLE consultations ALTER COLUMN clinical_representation_embedding TYPE vector(768);"))
        await session.commit()
        print("SUCCESSFULLY ALTERED consultations.clinical_representation_embedding TO vector(768)!")

asyncio.run(update_dim())
