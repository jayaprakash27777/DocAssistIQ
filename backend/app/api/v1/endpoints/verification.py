"""DocAssistIQ — Citation Verification Endpoints (Phase 38).

Endpoints:
  POST /verification/verify — Verify a specific claim and citation against the knowledge base.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.verification import ClaimVerificationRequest, ClaimVerificationResponse
from app.services.verification_service import verify_claim_citation

router = APIRouter(prefix="/verification", tags=["Citation Verification"])

@router.post(
    "/verify",
    response_model=ClaimVerificationResponse,
    summary="Verify claim against evidence",
    responses=API_RESPONSES,
)
async def verify_claim(
    request: ClaimVerificationRequest,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> ClaimVerificationResponse:
    """
    Verify that a claim is supported by a valid, active, and approved piece of evidence.
    """
    response = await verify_claim_citation(db, request)
    return response
