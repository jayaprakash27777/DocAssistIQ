from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.api.deps import get_db
from app.services.ingestion.medication_ingester import medication_ingester

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
