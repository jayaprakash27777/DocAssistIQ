import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.clinical import ClinicalFinding
from app.models.consultation import Consultation
from app.models.provenance import Evidence, Article, Source
from app.models.embedding import EmbeddingRecord
from app.schemas.explanation import ExplanationResponse, ExplanationEvidenceItem
from app.schemas.rag import RAGQueryRequest, RAGFilterParams
from app.services.rag_service import retrieve_evidence

logger = logging.getLogger(__name__)

async def explain_clinical_finding(db: AsyncSession, finding_id: uuid.UUID) -> ExplanationResponse:
    """
    Generate an auditable explanation for a specific clinical finding.
    Does not expose raw chain-of-thought, but rather pieces together the 
    underlying DB state that justifies the finding.
    """
    # 1. Fetch the target finding
    stmt = select(ClinicalFinding).where(ClinicalFinding.id == finding_id)
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Clinical finding not found"
        )

    # 2. Fetch other findings in the same consultation
    stmt_others = select(ClinicalFinding).where(
        ClinicalFinding.consultation_id == finding.consultation_id,
        ClinicalFinding.id != finding_id
    )
    others_result = await db.execute(stmt_others)
    other_findings = others_result.scalars().all()

    supporting_findings = []
    contradicting_findings = []
    
    for other in other_findings:
        # Heuristic rules:
        # If it's a symptom that maps to the same concept, it's supporting
        if finding.concept and other.concept and finding.concept in other.concept:
            supporting_findings.append(other.finding_text)
        # If it's the exact opposite negation state
        elif finding.negated != other.negated and finding.concept == other.concept:
            contradicting_findings.append(other.finding_text)

    # 3. Retrieve Supporting Evidence via RAG (simulating a search using the finding text)
    # We use the existing safe RAG service
    rag_request = RAGQueryRequest(
        query=finding.finding_text,
        top_k=3,
        filters=RAGFilterParams(only_approved=True)
    )
    rag_response = await retrieve_evidence(db, rag_request)
    
    supporting_evidence = []
    for cit in rag_response.citations:
        try:
            ev_id = uuid.UUID(cit.evidence_id)
            supporting_evidence.append(ExplanationEvidenceItem(
                evidence_id=ev_id,
                source_name=cit.source_name,
                source_status="active",
                is_production_suitable=True,
                evidence_grade=cit.evidence_grade,
                claim=cit.claim
            ))
        except ValueError:
            pass

    # 4. Synthesize Missing Information and Safety Flags (Mock heuristics based on text)
    missing_information = []
    safety_flags = []
    
    if finding.finding_type == "diagnosis":
        missing_information.append("Recent lab results not found in transcript.")
        
    if "pain" in finding.finding_text.lower() and not finding.certainty:
        missing_information.append("Severity/Scale of pain not mentioned.")
        
    if "allergy" in finding.finding_text.lower():
        safety_flags.append("Patient reported allergy; verify before prescribing.")

    # In a real system, these would come from config or global state
    model_version = "DocAssistIQ-NLP-v2.4 (Clinical BERT)"
    knowledge_version = str(finding.knowledge_version_id) if finding.knowledge_version_id else "KB-LATEST-STABLE"

    return ExplanationResponse(
        finding_id=finding.id,
        supporting_findings=supporting_findings,
        contradicting_findings=contradicting_findings,
        missing_information=missing_information,
        linked_investigations=[], # Placeholder for Phase 39
        supporting_evidence=supporting_evidence,
        safety_flags=safety_flags,
        model_version=model_version,
        knowledge_version=knowledge_version
    )
