"""DocAssistIQ — Authentication Pydantic Schemas.

All schemas are strict-mode Pydantic v2 models. Password fields are
write-only (input only). ``password_hash`` never appears here.

Password rules (NIST SP 800-63B baseline):
  - Minimum 8 characters.
  - At least one uppercase, one lowercase, one digit.
  - Maximum 128 characters (prevents bcrypt DoS via long inputs).
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for POST /api/v1/auth/register."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(description="Clinician email address (used as login)")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must contain upper, lower, digit)",
    )
    full_name: str = Field(
        min_length=2,
        max_length=200,
        description="Clinician full name as displayed in the UI",
    )

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Enforce minimum complexity requirements."""
        errors: list[str] = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if errors:
            msg = "Password must contain " + ", ".join(errors)
            raise ValueError(msg)
        return v


class LoginRequest(BaseModel):
    """Request body for POST /api/v1/auth/login."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Response body for POST /api/v1/auth/login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")


class MeResponse(BaseModel):
    """Response body for GET /api/v1/auth/me and POST /api/v1/auth/register."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    permissions: list[str] = []
    created_at: datetime
    updated_at: datetime
