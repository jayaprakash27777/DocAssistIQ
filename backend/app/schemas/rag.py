import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RAGFilterParams(BaseModel):
    """Filters to apply when retrieving evidence from the knowledge base."""
    min_evidence_grade: Optional[str] = Field(
        None, description="Minimum EBM grade (e.g. 'IIa'). If None, returns any."
    )
    only_approved: bool = Field(
        True, description="Only retrieve evidence linked to APPROVED entities."
    )
    knowledge_version_id: Optional[uuid.UUID] = Field(
        None, description="Limit to a specific knowledge version snapshot."
    )


class RAGQueryRequest(BaseModel):
    """Request payload for RAG retrieval."""
    query: str = Field(..., description="The clinical query string.")
    patient_context: Optional[str] = Field(
        None, description="Optional patient state (e.g. '70yo M with CKD')."
    )
    filters: RAGFilterParams = Field(default_factory=RAGFilterParams)
    top_k: int = Field(5, description="Number of evidence chunks to retrieve.")


class RAGCitation(BaseModel):
    """A specific piece of retrieved evidence mapped to a source."""
    evidence_id: uuid.UUID
    claim: str
    evidence_grade: Optional[str] = None
    recommendation_grade: Optional[str] = None
    source_name: str
    source_code: str
    article_doi: Optional[str] = None
    entity_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RAGResponse(BaseModel):
    """Response payload for RAG retrieval."""
    query: str
    answer: str
    insufficient_evidence: bool = Field(
        ..., description="True if no reliable evidence was found above baseline thresholds."
    )
    citations: List[RAGCitation]

    model_config = ConfigDict(from_attributes=True)
