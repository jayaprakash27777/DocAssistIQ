import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class ExplanationEvidenceItem(BaseModel):
    """An individual piece of supporting evidence for an explanation."""
    evidence_id: uuid.UUID
    source_name: str
    source_status: str
    is_production_suitable: bool
    evidence_grade: Optional[str]
    claim: str
    
    model_config = ConfigDict(from_attributes=True)


class ExplanationResponse(BaseModel):
    """The auditable explanation for a clinical finding or suggestion."""
    finding_id: uuid.UUID
    supporting_findings: List[str] = Field(default_factory=list, description="Other findings that support this.")
    contradicting_findings: List[str] = Field(default_factory=list, description="Findings that might contradict this.")
    missing_information: List[str] = Field(default_factory=list, description="Missing clinical context needed to be certain.")
    linked_investigations: List[str] = Field(default_factory=list, description="Relevant prior investigations.")
    supporting_evidence: List[ExplanationEvidenceItem] = Field(default_factory=list, description="Approved knowledge base evidence.")
    safety_flags: List[str] = Field(default_factory=list, description="Any critical safety or contraindication flags.")
    model_version: str = Field(..., description="The version of the ML model that generated this finding.")
    knowledge_version: str = Field(..., description="The ID/version of the knowledge base active at the time.")
