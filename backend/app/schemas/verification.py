import uuid
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class ClaimVerificationRequest(BaseModel):
    """Request payload for verifying a single claim."""
    evidence_id: uuid.UUID = Field(..., description="The unique ID of the evidence cited.")
    claim_text: str = Field(..., description="The claim text that is citing the evidence.")

class EvidenceDetails(BaseModel):
    """Details of the evidence if it was found."""
    source_name: str
    source_status: str
    is_production_suitable: bool
    evidence_grade: Optional[str]
    actual_claim: str
    is_ai_extracted: bool
    reviewed_by_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)

class ClaimVerificationResponse(BaseModel):
    """Response indicating the verification status of a claim."""
    is_verified: bool = Field(..., description="True if the claim is fully supported and verified.")
    status: Literal["VERIFIED", "FABRICATED_ID", "INVALID_SOURCE", "UNAPPROVED_EVIDENCE", "MISMATCHED_CLAIM"]
    reason: str = Field(..., description="Human-readable explanation of the status.")
    evidence_details: Optional[EvidenceDetails] = None

    model_config = ConfigDict(from_attributes=True)
