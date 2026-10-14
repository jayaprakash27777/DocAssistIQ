import asyncio
from app.infrastructure.database import get_session_factory
from sqlalchemy import text

async def update():
    session_factory = get_session_factory()
    async with session_factory() as session:
        res = await session.execute(
            text("UPDATE doctors SET verification_status = 'verified' WHERE verification_status != 'verified'")
        )
        await session.commit()
        print("Updated rows:", res.rowcount)

if __name__ == "__main__":
    asyncio.run(update())
