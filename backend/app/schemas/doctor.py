"""DocAssistIQ — Doctor Profile Schemas (Phase 10).

Request/response schemas for the Doctor profile and verification workflow.

Verification state machine:
  pending → verified  (admin action)
  pending → rejected  (admin action with required reason)
  rejected → pending  (doctor re-submission)
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Doctor response ───────────────────────────────────────────


class DoctorResponse(BaseModel):
    """Public representation of a Doctor profile."""

    id: UUID
    user_id: UUID
    tenant_id: UUID | None
    specialty: str | None
    credential_reference: str | None
    credential_body: str | None
    bio: str | None
    verification_status: Literal["pending", "verified", "rejected"]
    rejection_reason: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ── Create / update ───────────────────────────────────────────


class DoctorCreate(BaseModel):
    """Doctor submits their profile for verification."""

    specialty: str | None = Field(
        default=None,
        max_length=120,
        description="Medical specialty",
    )
    credential_reference: str | None = Field(
        default=None,
        max_length=200,
        description="Medical registration / license number (opaque reference)",
    )
    credential_body: str | None = Field(
        default=None,
        max_length=120,
        description="Issuing body (e.g. 'GMC', 'NMC', 'MCI')",
    )
    bio: str | None = Field(
        default=None,
        max_length=2000,
        description="Professional biography",
    )


class DoctorUpdate(BaseModel):
    """Doctor updates their profile (resets to pending if submitted credentials change)."""

    specialty: str | None = Field(default=None, max_length=120)
    credential_reference: str | None = Field(default=None, max_length=200)
    credential_body: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)


# ── Admin verification actions ────────────────────────────────


class VerifyDoctorRequest(BaseModel):
    """Admin approves doctor verification."""

    action: Literal["verify", "reject"] = Field(
        description="'verify' to approve, 'reject' to decline",
    )
    rejection_reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Required when action='reject'. Must be non-empty.",
    )

    @field_validator("rejection_reason")
    @classmethod
    def require_reason_for_rejection(
        cls, v: str | None, info: object
    ) -> str | None:
        values = getattr(info, "data", {})
        if values.get("action") == "reject" and not v:
            raise ValueError("rejection_reason is required when action='reject'")
        return v
