from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field

class PostAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    file_url: str
    file_type: str
    created_at: datetime

class PostCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Comment content")

class PostCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    post_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    created_at: datetime
    author_name: Optional[str] = None
    author_specialty: Optional[str] = None
    author_institution: Optional[str] = None
    author_credentials: Optional[str] = None

class DoctorPostCreate(BaseModel):
    disease_name: str = Field(..., description="Name of the disease/condition")
    clinical_findings: str = Field(..., description="Key clinical findings and presentation")
    diagnosis: str = Field(..., description="Final or differential diagnosis")
    treatment_plan: str = Field(..., description="Detailed treatment plan")
    drugs_used: List[str] = Field(default_factory=list, description="List of generic drugs used")
    specialty_tags: List[str] = Field(default_factory=list, description="Specialties this post is related to")
    attachment_ids: List[uuid.UUID] = Field(default_factory=list, description="IDs of previously uploaded files")
    case_status: Optional[str] = "active"  # "active" | "solved" | "urgent_consult"
    is_urgent_consult: Optional[bool] = False
    poll_question: Optional[str] = None
    poll_options: Optional[List[str]] = None
    quoted_post_id: Optional[uuid.UUID] = None

class QuotedPostSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_name: str
    author_specialty: Optional[str] = None
    author_institution: Optional[str] = None
    disease_name: str
    diagnosis: str
    clinical_findings: str
    created_at: datetime
    is_urgent_consult: bool = False

class ClinicalReactionCreate(BaseModel):
    reaction_type: str = Field("validate", description="validate | insightful | rare | endorsed | flag")

class PollVoteCreate(BaseModel):
    option_index: int = Field(..., ge=0, le=5, description="Index of selected poll option")

class DoctorPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_id: uuid.UUID
    disease_name: str
    clinical_findings: str
    diagnosis: str
    treatment_plan: str
    drugs_used: List[str]
    specialty_tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    likes_count: int = 0
    comments_count: int = 0
    is_liked_by_me: bool = False
    is_bookmarked_by_me: bool = False

    # Enhanced Verified Doctor Identity
    author_name: Optional[str] = None
    author_specialty: Optional[str] = None
    author_institution: Optional[str] = None
    author_credentials: Optional[str] = None
    author_avatar: Optional[str] = None
    is_author_verified: bool = True

    # Real-Time Clinical Dynamics
    case_status: Optional[str] = "active"
    is_urgent_consult: bool = False
    endorsements_count: int = 0
    is_endorsed_by_me: bool = False
    reactions_breakdown: Dict[str, int] = Field(default_factory=lambda: {"validate": 0, "insightful": 0, "rare": 0, "endorsed": 0, "flag": 0})
    my_reaction: Optional[str] = None
    poll_data: Optional[Dict[str, Any]] = None
    ai_knowledge_weight: int = 98
    
    attachments: List[PostAttachmentResponse] = Field(default_factory=list)
    comments: List[PostCommentResponse] = Field(default_factory=list) # Truncated to top 3 for feed
    quoted_post_id: Optional[uuid.UUID] = None
    quoted_post: Optional[QuotedPostSummary] = None

