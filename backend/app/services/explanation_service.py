import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.clinical import ClinicalFinding
from app.models.consultation import Consultation
from app.models.provenance import Evidence, Article, Source
from app.models.embedding import EmbeddingRecord
from app.models.knowledge import Disease
from app.schemas.explanation import ExplanationResponse, ExplanationEvidenceItem
from app.schemas.rag import RAGQueryRequest, RAGFilterParams
from app.services.rag_service import retrieve_evidence
from app.services.graph_service import get_disease_knowledge_graph

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
        patient_context=None,
        top_k=3,
        filters=RAGFilterParams(only_approved=True, min_evidence_grade="LOW", knowledge_version_id=None)
    )
    rag_response = await retrieve_evidence(db, rag_request)
    
    supporting_evidence = []
    for cit in rag_response.citations:
        try:
            ev_id = cit.evidence_id if isinstance(cit.evidence_id, uuid.UUID) else uuid.UUID(cit.evidence_id)
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

    # 4. Synthesize Missing Information and Safety Flags
    missing_information = []
    safety_flags = []
    linked_investigations = []
    
    if finding.finding_type == "diagnosis" and finding.concept:
        # Phase 40: Use Knowledge Graph for real disease explanations
        stmt_disease = select(Disease).where(Disease.name.ilike(finding.concept))
        disease_res = await db.execute(stmt_disease)
        disease = disease_res.scalar_one_or_none()
        
        if disease:
            graph = await get_disease_knowledge_graph(db, disease.id)
            
            # Use graph edges to find expected symptoms, investigations, medicines
            expected_symptoms = [n.name for n in graph.nodes if n.node_type == 'symptom']
            investigations = [n.name for n in graph.nodes if n.node_type == 'investigation']
            medicines = [n.name for n in graph.nodes if n.node_type == 'medicine']
            
            linked_investigations.extend(investigations)
            
            # Check if expected symptoms are missing from the consultation
            consultation_text = " ".join([f.finding_text.lower() for f in other_findings])
            for sym in expected_symptoms:
                if sym.lower() not in consultation_text:
                    missing_information.append(f"Missing expected symptom for {disease.name}: {sym}")
                    
            for med in medicines:
                if med.lower() in consultation_text:
                    # If they are on a medicine for this disease, check for contraindications
                    for edge in graph.edges:
                        if edge.relationship == 'contraindicated_for':
                            target_node = next((n for n in graph.nodes if n.id == edge.target_id), None)
                            if target_node and target_node.name.lower() in consultation_text:
                                safety_flags.append(f"Contraindication: {med} is contraindicated for {target_node.name}")
        else:
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
        linked_investigations=linked_investigations,
        supporting_evidence=supporting_evidence,
        safety_flags=safety_flags,
        model_version=model_version,
        knowledge_version=knowledge_version
    )
