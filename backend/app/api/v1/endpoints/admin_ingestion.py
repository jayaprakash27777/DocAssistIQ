from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.dependencies import get_db
from app.services.ingestion.medication_ingester import medication_ingester
from app.services.ingestion.social_ingester import ingest_doctor_post
from app.models.social import DoctorPost
from sqlalchemy import select

router = APIRouter()

@router.post("/medications", response_model=Dict[str, Any])
async def ingest_medications(
    limit: int = Query(10, ge=1, le=100, description="Number of FDA records to fetch"),
    skip: int = Query(0, ge=0, description="Number of FDA records to skip"),
    db: AsyncSession = Depends(get_db)
    # Ideally, require an admin role dependency here
):
    """
    Triggers the ingestion of live FDA medication data.
    Downloads drug labels, contraindications, and warnings from OpenFDA.
    Automatically generates semantic embeddings for each drug and saves them.
    """
    try:
        ingested = await medication_ingester.ingest_batch(db=db, limit=limit, skip=skip)
        return {
            "status": "success",
            "message": f"Successfully fetched {limit} records from FDA.",
            "ingested_count": ingested
        }
    except Exception as e:
        import structlog
        structlog.get_logger(__name__).error("ingestion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/social-posts", response_model=Dict[str, Any])
async def ingest_social_posts(
    db: AsyncSession = Depends(get_db)
    # Ideally, require an admin role dependency here
):
    """
    Batch ingests all existing DoctorPosts into the AI knowledge base.
    Skips posts that already have identical embeddings (via content_hash).
    """
    try:
        stmt = select(DoctorPost)
        posts = (await db.execute(stmt)).scalars().all()
        
        count = 0
        for post in posts:
            await ingest_doctor_post(db, post)
            count += 1
            
        return {
            "status": "success",
            "message": "Batch ingestion of social posts completed.",
            "processed_count": count
        }
    except Exception as e:
        import structlog
        structlog.get_logger(__name__).error("social_batch_ingestion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Social ingestion failed: {str(e)}")

@router.post("/travel-notices", response_model=Dict[str, Any])
async def ingest_travel_notices(
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest CDC Travel Health Notices into the global knowledge database for RAG.
    """
    from app.services.ingestion.travel_notice_ingester import travel_notice_ingester
    
    try:
        docs_created = await travel_notice_ingester.ingest_batch(db)
        return {
            "status": "success",
            "message": "Successfully ingested travel notices.",
            "ingested_count": docs_created
        }
    except Exception as e:
        import structlog
        structlog.get_logger(__name__).error("travel_notices_ingestion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Travel notices ingestion failed: {str(e)}")
