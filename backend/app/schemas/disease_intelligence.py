from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.rag import RAGCitation

class DiseaseIntelligenceResponse(BaseModel):
    disease_name: str
    summary: str
    symptoms: List[str] = Field(default_factory=list)
    treatments: List[str] = Field(default_factory=list)
    investigations: List[str] = Field(default_factory=list)
    citations: List[RAGCitation] = Field(default_factory=list)
