import asyncio
from app.infrastructure.database import get_session_factory
from sqlalchemy import text

async def main():
    async with get_session_factory()() as db:
        res = await db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'doctor_posts'"))
        for row in res.fetchall():
            print(f"{row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(main())
