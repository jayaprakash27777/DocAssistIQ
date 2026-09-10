import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings

async def fix():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE symptoms ALTER COLUMN code TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE symptoms ALTER COLUMN name TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE diseases ALTER COLUMN code TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE diseases ALTER COLUMN name TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE diseases ALTER COLUMN category TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE investigations ALTER COLUMN code TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE investigations ALTER COLUMN name TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE medicines ALTER COLUMN code TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE medicines ALTER COLUMN name TYPE TEXT;"))
        await conn.execute(text("ALTER TABLE medicines ALTER COLUMN drug_class TYPE TEXT;"))
    await engine.dispose()
    print("Database columns successfully relaxed to TEXT!")

if __name__ == "__main__":
    asyncio.run(fix())
