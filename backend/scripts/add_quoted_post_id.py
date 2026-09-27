import asyncio
from app.infrastructure.database import get_session_factory
from sqlalchemy import text

async def main():
    async with get_session_factory()() as db:
        await db.execute(text("""
            ALTER TABLE doctor_posts 
            ADD COLUMN IF NOT EXISTS quoted_post_id UUID REFERENCES doctor_posts(id) ON DELETE SET NULL;
        """))
        await db.commit()
        print("Successfully added quoted_post_id column to doctor_posts table!")

if __name__ == "__main__":
    asyncio.run(main())
