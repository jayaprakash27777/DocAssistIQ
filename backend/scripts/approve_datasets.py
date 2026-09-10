import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.config import get_settings
from app.models.ingestion import IngestionJob

async def approve_jobs():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as session:
        async with session.begin():
            jobs = await session.execute(select(IngestionJob).where(IngestionJob.review_status == "unreviewed"))
            jobs = jobs.scalars().all()
            for job in jobs:
                job.review_status = "approved"
                print(f"Approved job {job.id} for source {job.source_id}")
                
    await engine.dispose()
    print("All unreviewed ingestion jobs have been marked as 'approved'!")

if __name__ == "__main__":
    asyncio.run(approve_jobs())
