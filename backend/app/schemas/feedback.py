from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ClinicianFeedbackCreate(BaseModel):
    suggestion_id: str = Field(..., max_length=100)
    suggestion_type: str = Field(..., max_length=50)
    decision: str = Field(..., max_length=20, description="'ACCEPT', 'MODIFY', 'REJECT'")
    reason: Optional[str] = None
    suggestion_context: Dict[str, Any]
    modified_context: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = "1.0.0"
    knowledge_version: Optional[str] = "1.0.0"

class ClinicianFeedbackResponse(BaseModel):
    id: str
    suggestion_id: str
    suggestion_type: str
    decision: str
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True
