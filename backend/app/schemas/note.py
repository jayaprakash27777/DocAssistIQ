from pydantic import BaseModel, ConfigDict
import uuid
from typing import Optional, Any, Dict
from datetime import datetime

class ClinicalNoteBase(BaseModel):
    body: dict
    status: str
    is_ai_generated: bool

class ClinicalNoteUpdate(BaseModel):
    """Update payload for a clinical note.
    
    Accepts either 'body' (full replacement) or 'sections' (partial update).
    If both are provided, sections are merged into body.
    """
    body: Optional[Dict[str, Any]] = None
    sections: Optional[Dict[str, str]] = None
    version: int  # Required for Optimistic Concurrency Control

    def get_merged_body(self, current_body: dict) -> dict:
        """Produce the new body dict by merging updates."""
        if self.body is not None:
            # Full replacement
            result = dict(self.body)
        else:
            result = dict(current_body) if current_body else {}
        if self.sections:
            result.update(self.sections)
        return result

class ClinicalNoteResponse(ClinicalNoteBase):
    id: uuid.UUID
    consultation_id: uuid.UUID
    author_id: uuid.UUID
    note_type: str
    version: int
    last_edited_by_id: Optional[uuid.UUID]
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)
