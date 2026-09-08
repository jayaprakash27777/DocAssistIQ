"""DocAssistIQ — Transcript Schemas (Phase 27)."""

import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TranscriptSegmentBase(BaseModel):
    start_time: float
    end_time: float
    speaker_label: Optional[str] = None
    speaker_confidence: Optional[float] = None
    speaker_source: Optional[str] = None
    raw_text: str
    processed_text: str
    clinician_corrected_text: Optional[str] = None
    is_corrected: bool = False


class TranscriptSegmentCreate(TranscriptSegmentBase):
    pass


class TranscriptSegmentResponse(TranscriptSegmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class TranscriptBase(BaseModel):
    status: str


class TranscriptCreate(TranscriptBase):
    segments: List[TranscriptSegmentCreate]


class TranscriptResponse(TranscriptBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    consultation_id: uuid.UUID
    segments: List[TranscriptSegmentResponse]


class TranscriptCorrection(BaseModel):
    clinician_corrected_text: str
