"""DocAssistIQ - Disease Intelligence API Endpoints (v3)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.dependencies import get_db
from app.schemas.disease_intelligence import DiseaseIntelligenceResponse
from app.services.disease_intelligence_service import generate_disease_intelligence

router = APIRouter(prefix="/intelligence", tags=["Disease Intelligence"])


@router.get(
    "/disease/{disease_name}",
    response_model=DiseaseIntelligenceResponse,
    summary="Deep clinical intelligence for any disease",
    description=(
        "Returns a comprehensive 20+ field clinical profile including: "
        "pathophysiology, etiology, epidemiology, red flags, stages, prognosis, "
        "complications, management, monitoring, prevention, and special populations. "
        "Sources: Wikipedia, ICD-11, PubMed, WHO/CDC, RAG, dynamic KB."
    ),
)
async def get_disease_intelligence(
    disease_name: str,
    consultation_id: Optional[str] = Query(None, description="Optional consultation context"),
    db: AsyncSession = Depends(get_db),
) -> DiseaseIntelligenceResponse:
    return await generate_disease_intelligence(db, disease_name)
