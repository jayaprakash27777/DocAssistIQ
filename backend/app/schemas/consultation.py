"""DocAssistIQ — Consultation Pydantic Schemas.

Clinical safety:
  All response schemas include ``is_placeholder = True`` so the UI always
  knows whether it is displaying a real clinical result or a placeholder.
  The placeholder label is enforced here and in the service layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── PLACEHOLDER safety label (must appear in every placeholder response) ──
PLACEHOLDER_LABEL = "PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL"


class ConsultationCreate(BaseModel):
    """Input for creating a new consultation."""

    input_text: str = Field(
        ...,
        min_length=10,
        max_length=10_000,
        description=(
            "Clinical scenario text entered by the clinician. "
            "Must not contain patient-identifiable data in development."
        ),
        examples=["Patient presents with chest pain radiating to the left arm."],
    )


class ConsultationResponse(BaseModel):
    """Full consultation record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    input_text: str
    status: str
    placeholder_response: str | None
    is_placeholder: bool = True  # always True in Phase 8
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConsultationSummary(BaseModel):
    """Abbreviated consultation record for list views."""

    id: uuid.UUID
    status: str
    is_placeholder: bool = True
    input_preview: str  # first 120 chars of input_text
    created_at: datetime

    model_config = {"from_attributes": True}

class ConsultationAuditResponse(BaseModel):
    id: uuid.UUID
    consultation_id: uuid.UUID
    from_status: str | None
    to_status: str
    actor_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
