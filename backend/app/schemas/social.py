from typing import List, Optional
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

class DoctorPostCreate(BaseModel):
    disease_name: str = Field(..., description="Name of the disease/condition")
    clinical_findings: str = Field(..., description="Key clinical findings and presentation")
    diagnosis: str = Field(..., description="Final or differential diagnosis")
    treatment_plan: str = Field(..., description="Detailed treatment plan")
    drugs_used: List[str] = Field(default_factory=list, description="List of generic drugs used")
    specialty_tags: List[str] = Field(default_factory=list, description="Specialties this post is related to")
    attachment_ids: List[uuid.UUID] = Field(default_factory=list, description="IDs of previously uploaded files")

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
    
    attachments: List[PostAttachmentResponse] = Field(default_factory=list)
    comments: List[PostCommentResponse] = Field(default_factory=list) # Truncated to top 3 for feed
