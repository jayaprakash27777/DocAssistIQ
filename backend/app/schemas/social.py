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

class TreatmentSuggestionCreate(BaseModel):
    drug_or_intervention: str = Field(..., description="Suggested medication, regimen, or procedure")
    dosage_and_route: Optional[str] = Field(None, description="Dosage and route")
    clinical_rationale: str = Field(..., description="Clinical reasoning and guidelines")
    evidence_grade: Optional[str] = Field(None, description="Guideline evidence tier")

class TreatmentSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    post_id: uuid.UUID
    author_id: uuid.UUID
    author_name: str
    author_specialty: str
    author_institution: Optional[str] = None
    author_credentials: Optional[str] = None
    drug_or_intervention: str
    dosage_and_route: Optional[str] = None
    clinical_rationale: str
    evidence_grade: Optional[str] = None
    endorsements_count: int = 0
    is_adopted: bool = False
    created_at: datetime

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
    thread_stages: Optional[List[Dict[str, Any]]] = None

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
    bookmark_folder: Optional[str] = None

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
    is_solved: bool = False
    patient_outcome: Optional[str] = None
    outcome_reported_at: Optional[str] = None
    author_country: Optional[str] = None
    author_license_body: Optional[str] = None
    endorsements_count: int = 0
    is_endorsed_by_me: bool = False
    reactions_breakdown: Dict[str, int] = Field(default_factory=lambda: {"validate": 0, "insightful": 0, "rare": 0, "endorsed": 0, "flag": 0})
    my_reaction: Optional[str] = None
    poll_data: Optional[Dict[str, Any]] = None
    ai_knowledge_weight: int = 98
    
    attachments: List[PostAttachmentResponse] = Field(default_factory=list)
    comments: List[PostCommentResponse] = Field(default_factory=list) # Truncated to top 3 for feed
    treatment_suggestions: List[TreatmentSuggestionResponse] = Field(default_factory=list)
    quoted_post_id: Optional[uuid.UUID] = None
    quoted_post: Optional[QuotedPostSummary] = None
    thread_stages: Optional[List[Dict[str, Any]]] = None

class PostOutcomeUpdate(BaseModel):
    patient_outcome: str
    is_solved: bool = True

class CurbsideMessageCreate(BaseModel):
    post_id: uuid.UUID
    receiver_id: uuid.UUID
    content: str

class CurbsideMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    post_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    sender_specialty: str
    receiver_id: uuid.UUID
    content: str
    created_at: datetime
    is_read: bool = False

class BookmarkFolderUpdate(BaseModel):
    folder_name: str



# ─── Doctor Circles (Facebook Groups Style) ───────────────────────────────────

class CircleResponse(BaseModel):
    id: str
    name: str
    icon: str
    specialty: str
    description: str
    member_count: int
    weekly_cases_count: int
    is_joined: bool
    tags: List[str]

class CircleJoinResponse(BaseModel):
    id: str
    is_joined: bool
    member_count: int


# ─── Hospital Grand Rounds & CME Events (Facebook Events Style) ───────────────

class CMEEventResponse(BaseModel):
    id: str
    title: str
    specialty: str
    date: str
    time: str
    speaker: str
    speaker_title: str
    cme_credits: float
    location: str
    rsvp_count: int
    is_attending: bool
    topics: List[str]

class EventRSVPResponse(BaseModel):
    id: str
    is_attending: bool
    rsvp_count: int


# ─── Grand Rounds Audio Spaces (Twitter Spaces Style) ─────────────────────────

class AudioSpaceSpeaker(BaseModel):
    id: str
    name: str
    specialty: str
    role: str  # host, speaker, listener
    is_speaking: bool
    avatar_gradient: str

class AudioSpaceResponse(BaseModel):
    id: str
    title: str
    specialty: str
    listeners_count: int
    is_live: bool
    active_case_title: str
    speakers: List[AudioSpaceSpeaker]
    tags: List[str]


# ─── Clinical Reels & Diagnostic Snaps (Instagram Style) ──────────────────────

class ReelQuizOption(BaseModel):
    label: str
    is_correct: bool
    explanation: str
    peer_percentage: int

class ClinicalReelResponse(BaseModel):
    id: str
    title: str
    disease_name: str
    specialty: str
    author_name: str
    author_credentials: str
    media_url: str
    media_type: str
    clinical_pearl: str
    audio_type: Optional[str] = None
    quiz_question: Optional[str] = None
    quiz_options: List[ReelQuizOption] = Field(default_factory=list)
    likes_count: int
    comments_count: int
    shares_count: int
    is_liked: bool = False


# ─── Real-Time Drug-Drug Interaction (DDI) Safety Engine ───────────────────────

class DDICheckRequest(BaseModel):
    drugs: List[str]

class DDIInteractionItem(BaseModel):
    drug1: str
    drug2: str
    severity: str  # CONTRAINDICATED, MAJOR, MODERATE, MINOR
    mechanism: str
    clinical_effect: str
    recommendation: str
    evidence_level: str

class DDICheckResponse(BaseModel):
    analyzed_drugs: List[str]
    has_contraindications: bool
    highest_severity: str
    interactions: List[DDIInteractionItem]
    safety_summary: str


# ─── Doctor-to-Doctor Curbside Consult Messenger (Facebook Messenger Style) ───

class CurbsideMessageCreate(BaseModel):
    peer_doctor_id: Optional[str] = None
    receiver_id: Optional[uuid.UUID] = None
    content: str
    priority: str = "routine"  # routine | stat
    case_id: Optional[str] = None
    post_id: Optional[uuid.UUID] = None
    has_voice_note: bool = False
    voice_duration: Optional[int] = None

class CurbsideMessageResponse(BaseModel):
    id: str
    sender_doctor_id: str
    recipient_doctor_id: str
    sender_name: str
    sender_specialty: str
    content: str
    priority: str = "routine"
    case_id: Optional[str] = None
    case_title: Optional[str] = None
    post_id: Optional[str] = None
    has_voice_note: bool = False
    voice_duration: Optional[int] = None
    created_at: datetime
    is_read: bool = True



class DoctorCircleResponse(BaseModel):
    id: str
    name: str
    icon: str
    specialty: str
    description: str
    member_count: int
    weekly_cases_count: int
    is_joined: bool
    tags: List[str]


class CMEEventResponse(BaseModel):
    id: str
    title: str
    specialty: str
    date: str
    time: str
    speaker: str
    speaker_title: str
    cme_credits: float
    location: str
    rsvp_count: int
    is_attending: bool
    topics: List[str]



