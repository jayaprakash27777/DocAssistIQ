"""DocAssistIQ — Clinical Explanation Endpoints (Phase 39).

Endpoints:
  GET /explanation/{finding_id} — Get an auditable explanation for a clinical finding.
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.explanation import ExplanationResponse
from app.services.explanation_service import explain_clinical_finding

router = APIRouter(prefix="/explanation", tags=["Clinical Explanation"])

@router.get(
    "/{finding_id}",
    response_model=ExplanationResponse,
    summary="Get auditable explanation for finding",
    responses=API_RESPONSES,
)
async def get_finding_explanation(
    finding_id: uuid.UUID,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> ExplanationResponse:
    """
    Retrieve an auditable explanation for why a specific finding was generated.
    Returns supporting evidence, missing info, and credibility flags.
    """
    return await explain_clinical_finding(db, finding_id)
