import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from difflib import SequenceMatcher

from app.models.provenance import Evidence, Article, Source
from app.schemas.verification import ClaimVerificationRequest, ClaimVerificationResponse, EvidenceDetails

logger = logging.getLogger(__name__)

import re

def _calculate_semantic_similarity(claim1: str, claim2: str) -> float:
    """
    Multi-faceted clinical semantic similarity:
    1. Token-level Jaccard overlap (excluding common English stopwords).
    2. Bigram overlap for multi-word clinical phrases.
    3. Character-level SequenceMatcher ratio for inflectional robustness.
    Combines into an ensemble score [0.0, 1.0].
    """
    c1 = claim1.lower().strip()
    c2 = claim2.lower().strip()
    if not c1 or not c2:
        return 0.0
    if c1 == c2:
        return 1.0

    stopwords = {
        "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "of", "for",
        "with", "as", "by", "that", "this", "it", "from", "be", "or", "are", "was", "were"
    }
    
    tokens1 = [w for w in re.findall(r"\w+", c1) if w not in stopwords]
    tokens2 = [w for w in re.findall(r"\w+", c2) if w not in stopwords]
    
    if not tokens1 or not tokens2:
        return SequenceMatcher(None, c1, c2).ratio()
        
    set1, set2 = set(tokens1), set(tokens2)
    token_jaccard = len(set1.intersection(set2)) / max(len(set1.union(set2)), 1)
    
    # Bigram overlap
    bigrams1 = set(zip(tokens1[:-1], tokens1[1:])) if len(tokens1) > 1 else set()
    bigrams2 = set(zip(tokens2[:-1], tokens2[1:])) if len(tokens2) > 1 else set()
    bigram_jaccard = 0.0
    if bigrams1 and bigrams2:
        bigram_jaccard = len(bigrams1.intersection(bigrams2)) / max(len(bigrams1.union(bigrams2)), 1)
        
    seq_ratio = SequenceMatcher(None, c1, c2).ratio()
    
    # Substring containment boost
    contains_boost = 0.3 if (c1 in c2 or c2 in c1) else 0.0
    
    ensemble = (0.45 * token_jaccard) + (0.25 * bigram_jaccard) + (0.30 * seq_ratio) + contains_boost
    return min(round(ensemble, 3), 1.0)



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
