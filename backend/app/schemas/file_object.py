"""DocAssistIQ — File Object Schemas (Phase 11)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FileObjectResponse(BaseModel):
    """Public representation of a FileObject metadata record."""

    id: UUID
    owner_id: UUID
    tenant_id: UUID | None
    original_filename: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str | None
    status: str
    scan_status: str
    linked_entity_type: str | None
    linked_entity_id: UUID | None
    created_at: datetime | str
    updated_at: datetime | str

    model_config = {"from_attributes": True}


class FileDownloadUrlResponse(BaseModel):
    """Presigned download URL response."""

    file_id: UUID
    download_url: str
    expires_in_seconds: int = Field(
        description="Seconds until the presigned URL expires",
    )


class FileUploadResponse(BaseModel):
    """Response after a successful file upload."""

    file: FileObjectResponse
    message: str = "File uploaded successfully."
