import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from difflib import SequenceMatcher

from app.models.provenance import Evidence, Article, Source
from app.schemas.verification import ClaimVerificationRequest, ClaimVerificationResponse, EvidenceDetails

logger = logging.getLogger(__name__)

def _calculate_semantic_similarity(claim1: str, claim2: str) -> float:
    """
    Very basic semantic similarity for Phase 38 using difflib.
    In a real-world scenario, this would use a fast cross-encoder or vector similarity.
    """
    return SequenceMatcher(None, claim1.lower(), claim2.lower()).ratio()


async def verify_claim_citation(
    db: AsyncSession, request: ClaimVerificationRequest
) -> ClaimVerificationResponse:
    """
    Verify a claim against the database provenance rules.
    """
    stmt = (
        select(Evidence, Article, Source)
        .join(Article, Evidence.article_id == Article.id)
        .join(Source, Article.source_id == Source.id)
        .where(Evidence.id == request.evidence_id)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        return ClaimVerificationResponse(
            is_verified=False,
            status="FABRICATED_ID",
            reason="The provided evidence ID does not exist in the knowledge base."
        )

    evidence, article, source = row

    details = EvidenceDetails(
        source_name=source.name,
        source_status=source.status,
        is_production_suitable=source.is_production_suitable,
        evidence_grade=evidence.evidence_grade,
        actual_claim=evidence.claim,
        is_ai_extracted=evidence.is_ai_extracted,
        reviewed_by_id=evidence.reviewed_by_id,
    )

    # Check Source constraints
    if source.status != "active" or not source.is_production_suitable:
        return ClaimVerificationResponse(
            is_verified=False,
            status="INVALID_SOURCE",
            reason=f"The underlying source '{source.name}' is not approved for production use.",
            evidence_details=details
        )

    # Check Evidence constraints (e.g. AI-extracted but not reviewed)
    if evidence.is_ai_extracted and evidence.reviewed_by_id is None:
        return ClaimVerificationResponse(
            is_verified=False,
            status="UNAPPROVED_EVIDENCE",
            reason="The evidence was extracted by AI and has not yet been approved by a clinician.",
            evidence_details=details
        )

    # Check semantic similarity (simple heuristic)
    similarity = _calculate_semantic_similarity(request.claim_text, evidence.claim)
    if similarity < 0.2:
        return ClaimVerificationResponse(
            is_verified=False,
            status="MISMATCHED_CLAIM",
            reason="The text claim does not semantically match the cited evidence.",
            evidence_details=details
        )

    return ClaimVerificationResponse(
        is_verified=True,
        status="VERIFIED",
        reason="Claim is fully supported by approved evidence.",
        evidence_details=details
    )
