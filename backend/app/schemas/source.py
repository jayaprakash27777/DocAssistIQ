"""DocAssistIQ — Source Management Schemas (Phase 12)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class SourceBase(BaseModel):
    """Base attributes for a medical knowledge source."""

    code: Annotated[str, StringConstraints(min_length=2, max_length=80, pattern=r"^[a-z0-9_]+$")] = Field(
        description="Internal unique code (e.g. 'pubmed', 'rxnorm', 'who_guidelines')"
    )
    organisation: Annotated[str, StringConstraints(min_length=2, max_length=200)] = Field(
        description="Publishing organisation (e.g. 'NIH / NLM', 'WHO')"
    )
    name: Annotated[str, StringConstraints(min_length=2, max_length=200)] = Field(
        description="Source name (e.g. 'PubMed Central', 'RxNorm')"
    )
    base_url: str | None = Field(default=None, description="Base URL or API endpoint")
    access_mechanism: str = Field(
        default="api",
        description="'api' | 'bulk_download' | 'manual' | 'licensed_feed'",
    )
    data_type: str = Field(
        description="'literature' | 'drug_database' | 'clinical_guidelines' | 'coding_system'"
    )
    license_info: str | None = Field(
        default=None,
        description="License / access terms (must be verified before ingestion)",
    )


class SourceCreate(SourceBase):
    """Payload to register a new source."""


class SourceUpdate(BaseModel):
    """Payload to update an existing source."""

    organisation: Annotated[str, StringConstraints(min_length=2, max_length=200)] | None = None
    name: Annotated[str, StringConstraints(min_length=2, max_length=200)] | None = None
    base_url: str | None = None
    access_mechanism: str | None = None
    data_type: str | None = None
    license_info: str | None = None


class SourceResponse(SourceBase):
    """Public representation of a Source."""

    id: UUID
    is_production_suitable: bool
    last_verified_at: str | None
    status: str
    created_at: datetime | str
    updated_at: datetime | str

    model_config = ConfigDict(from_attributes=True)
