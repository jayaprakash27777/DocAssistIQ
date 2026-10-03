"""DocAssistIQ — Knowledge Review Endpoints (Phase 14).

Endpoints:
  GET    /knowledge/{entity_type}/pending — List knowledge entities pending review
  POST   /knowledge/{entity_type}/{id}/review — Transition status (approve, reject, supersede, etc.)
  GET    /knowledge/{entity_type}/{id}/provenance — Inspect provenance (evidence, source info)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse
from app.authorization import require_admin, require_doctor
from app.dependencies import get_db
from app.models.provenance import Article, Evidence, Source
from app.models.user import User
from app.schemas.knowledge import KnowledgeEntityResponse, KnowledgeReviewRequest, ProvenanceItemResponse
from app.services import knowledge_service
from app.services.audit_service import log_event
from app.services.embedding_service import generate_and_store_embedding
from app.models.embedding import EmbeddingRecord
from app.services.graph_service import get_disease_knowledge_graph
from app.schemas.graph import DiseaseKnowledgeGraph, GraphNode, GraphEdge

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base (Entities)"])





@router.get(
    "/{entity_type}/pending",
    response_model=PagedResponse[KnowledgeEntityResponse],
    summary="List pending knowledge",
    responses=API_RESPONSES,
)
async def list_pending_knowledge(
    entity_type: str,
    page: int = 1,
    page_size: int = 20,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PagedResponse[KnowledgeEntityResponse]:
    """List knowledge entities (disease, symptom, etc.) awaiting clinical review."""
    items, total = await knowledge_service.list_pending_knowledge(db, entity_type, page, page_size)
    pages = max(1, -(-total // page_size))
    
    return PagedResponse(
        items=[KnowledgeEntityResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post(
    "/{entity_type}/{entity_id}/review",
    response_model=KnowledgeEntityResponse,
    summary="Review knowledge entity",
    responses=API_RESPONSES,
)
async def review_knowledge(
    entity_type: str,
    entity_id: uuid.UUID,
    payload: KnowledgeReviewRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeEntityResponse:
    """Safely transition the status of a knowledge entity."""
    entity = await knowledge_service.transition_knowledge_status(
        db, entity_type, entity_id, payload.new_status, admin.id, payload.superseded_by_id
    )
    
    await log_event(
        db,
        action=f"knowledge.{payload.new_status}",
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=admin.id,
        severity="info",
    )
    
    return KnowledgeEntityResponse.model_validate(entity)


@router.get(
    "/{entity_type}/{entity_id}/provenance",
    response_model=list[ProvenanceItemResponse],
    summary="Inspect provenance evidence",
    responses=API_RESPONSES,
)
async def inspect_provenance(
    entity_type: str,
    entity_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ProvenanceItemResponse]:
    """Inspect the provenance/evidence details for a knowledge entity before review."""
    correct_result = await db.execute(
        select(Evidence, Article, Source)
        .join(Article, Evidence.article_id == Article.id)
        .join(Source, Article.source_id == Source.id)
        .where(Evidence.entity_type == entity_type)
        .where(Evidence.entity_id == entity_id)
    )
    
    provenance = []
    for evidence, article, source in correct_result:
        provenance.append(ProvenanceItemResponse(
            id=evidence.id,
            claim=evidence.claim,
            evidence_grade=evidence.evidence_grade,
            recommendation_grade=evidence.recommendation_grade,
            is_ai_extracted=evidence.is_ai_extracted,
            source_name=source.name,
            source_code=source.code,
        ))
        
    return provenance


class EmbeddingSyncResponse(BaseModel):
    id: uuid.UUID
    model: str
    dimensions: int
    generated_at: datetime | str

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/{entity_type}/{entity_id}/embeddings/sync",
    response_model=EmbeddingSyncResponse,
    summary="Generate embedding for entity",
    responses=API_RESPONSES,
)
async def sync_embedding(
    entity_type: str,
    entity_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EmbeddingSyncResponse:
    """Generate or retrieve the embedding vector for the specified entity via pgvector."""
    try:
        entity = await knowledge_service.get_knowledge_entity(db, entity_type, entity_id)
        name = getattr(entity, "name", "")
        code = getattr(entity, "code", "")
        desc = getattr(entity, "description", "") or ""
        extra = ""
        if entity_type == "disease":
            extra = f"\nSeverity: {getattr(entity, 'severity', 'unknown')}"
        elif entity_type == "medicine":
            extra = f"\nRoute: {getattr(entity, 'route', 'N/A')}\nClass: {getattr(entity, 'drug_class', 'N/A')}"
        content_to_embed = f"Clinical {entity_type.capitalize()}: {name} ({code})\nDescription: {desc}{extra}".strip()
    except Exception:
        content_to_embed = f"Knowledge Entity: {entity_type} {entity_id}"
    
    try:
        record = await generate_and_store_embedding(
            db=db,
            source_record_id=str(entity_id),
            source_record_type=entity_type,
            content=content_to_embed,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
    return EmbeddingSyncResponse(
        id=record.id,
        model=record.embedding_model,
        dimensions=record.dimensions,
        generated_at=record.generated_at.isoformat()
    )

@router.get(
    "/diseases/{disease_id}/graph",
    response_model=DiseaseKnowledgeGraph,
    summary="Get disease knowledge graph",
    responses=API_RESPONSES,
)
async def get_disease_graph(
    disease_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_doctor),
) -> DiseaseKnowledgeGraph:
    """
    Fetch the complete knowledge graph for a specific disease, including
    symptoms, investigations, medicines, and supporting evidence.
    """
    return await get_disease_knowledge_graph(db, disease_id)

@router.get(
    "/graph/by-disease/{disease_name}",
    response_model=DiseaseKnowledgeGraph,
    summary="Get disease knowledge graph by name",
    responses=API_RESPONSES,
)
async def get_disease_graph_by_name(
    disease_name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_doctor),
) -> DiseaseKnowledgeGraph:
    """
    Fetch the complete knowledge graph by disease name, including
    symptoms, investigations, medicines, and supporting evidence.
    """
    from app.models.knowledge import Disease
    clean_name = disease_name.strip()
    stmt = select(Disease).where(Disease.name.ilike(clean_name))
    res = await db.execute(stmt)
    disease = res.scalar_one_or_none()
    if not disease:
        stmt_fuzzy = select(Disease).where(Disease.name.ilike(f"%{clean_name}%"))
        res_fuzzy = await db.execute(stmt_fuzzy)
        disease = res_fuzzy.scalars().first()

    if not disease:
        from app.services.clinical_disease_metadata import get_disease_clinical_profile
        meta = get_disease_clinical_profile(clean_name)
        if meta:
            root_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"docassistiq.disease.{clean_name.lower()}")
            nodes = [
                GraphNode(id=root_id, code=meta.get("icd11_code") or "ICD-11", name=clean_name, category=meta.get("disease_class") or "Clinical Condition", node_type="disease")
            ]
            edges = []
            for s in meta.get("cardinal_symptoms", [])[:6]:
                s_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"docassistiq.symptom.{s.lower()}")
                nodes.append(GraphNode(id=s_id, code="SYM", name=s, node_type="symptom"))
                edges.append(GraphEdge(source_id=root_id, target_id=s_id, relationship="has_symptom", metadata={"frequency": "high", "specificity": "cardinal"}))
            for inv in meta.get("recommended_investigations", [])[:5]:
                i_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"docassistiq.inv.{inv.lower()}")
                nodes.append(GraphNode(id=i_id, code="INV", name=inv, node_type="investigation"))
                edges.append(GraphEdge(source_id=root_id, target_id=i_id, relationship="requires_investigation", metadata={"priority": "HIGH"}))
            for med in meta.get("recommended_medications", [])[:5]:
                m_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"docassistiq.med.{med.lower()}")
                nodes.append(GraphNode(id=m_id, code="MED", name=med, node_type="medicine"))
                edges.append(GraphEdge(source_id=root_id, target_id=m_id, relationship="indicated_medicine", metadata={"line": "first_line"}))
            return DiseaseKnowledgeGraph(disease_id=root_id, nodes=nodes, edges=edges)

        raise HTTPException(
            status_code=404,
            detail=f"Knowledge graph for '{disease_name}' not found",
        )
    return await get_disease_knowledge_graph(db, disease.id)

