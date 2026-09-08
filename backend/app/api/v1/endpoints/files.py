"""DocAssistIQ — File Upload/Download/Delete Endpoints (Phase 11).

Endpoints:
  POST   /files/upload        — upload a file (multipart/form-data)
  GET    /files/              — list own files (paginated)
  GET    /files/{id}/download — get presigned download URL
  DELETE /files/{id}          — delete a file

Security:
  - Only the file owner (or admin) can download or delete.
  - Uploads are validated for size, MIME type (server-side), and extension.
  - Object keys are server-generated — no user-controlled paths.
  - Files are never served directly — only presigned URLs.
  - Content-Disposition: attachment is enforced via MinIO presigned URL
    settings (no in-browser execution).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.file_object import (
    FileDownloadUrlResponse,
    FileObjectResponse,
    FileUploadResponse,
)
from app.services import file_service
from app.storage import get_storage_provider

router = APIRouter(prefix="/files", tags=["Files"])

PRESIGNED_URL_TTL = 3600  # 1 hour


# ── Dependency ────────────────────────────────────────────────


def get_storage():
    """FastAPI dependency that returns the singleton storage provider."""
    return get_storage_provider()


# ── Upload ────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=201,
    summary="Upload a file",
    description=(
        "Upload a file (multipart/form-data). "
        "Validated server-side for MIME type, size (max 50 MB), and extension. "
        "Returns a metadata record; use GET /files/{id}/download for access."
    ),
    responses=API_RESPONSES,
)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    linked_entity_type: str | None = Query(
        default=None,
        description="Optional entity type this file is attached to",
    ),
    linked_entity_id: uuid.UUID | None = Query(
        default=None,
        description="Optional entity UUID this file is attached to",
    ),
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
    storage=Depends(get_storage),
) -> FileUploadResponse:
    data = await file.read()
    client_mime = file.content_type or "application/octet-stream"
    filename = file.filename or "upload"

    file_obj = await file_service.upload_file(
        db=db,
        storage=storage,
        owner_id=user.id,
        data=data,
        filename=filename,
        client_mime=client_mime,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
    )

    return FileUploadResponse(
        file=FileObjectResponse.model_validate(file_obj),
    )


# ── List ──────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=PagedResponse[FileObjectResponse],
    summary="List own files",
    responses=API_RESPONSES,
)
async def list_files(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> PagedResponse[FileObjectResponse]:
    files, total = await file_service.list_my_files(db, user.id, page, page_size)
    pages = max(1, -(-total // page_size))
    return PagedResponse(
        items=[FileObjectResponse.model_validate(f) for f in files],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


# ── Download URL ──────────────────────────────────────────────


@router.get(
    "/{file_id}/download",
    response_model=FileDownloadUrlResponse,
    summary="Get presigned download URL",
    description=(
        "Returns a short-lived presigned URL (1 hour). "
        "Only the file owner or an admin can access this endpoint. "
        "Files are never served directly — always through presigned URLs."
    ),
    responses=API_RESPONSES,
)
async def get_download_url(
    file_id: uuid.UUID,
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
    storage=Depends(get_storage),
) -> FileDownloadUrlResponse:
    is_admin = user.role == "admin"
    url = await file_service.get_download_url(
        db=db,
        storage=storage,
        file_id=file_id,
        requester_id=user.id,
        is_admin=is_admin,
        expires_seconds=PRESIGNED_URL_TTL,
    )
    return FileDownloadUrlResponse(
        file_id=file_id,
        download_url=url,
        expires_in_seconds=PRESIGNED_URL_TTL,
    )


# ── Delete ────────────────────────────────────────────────────


@router.delete(
    "/{file_id}",
    status_code=204,
    summary="Delete a file",
    description=(
        "Permanently deletes a file from object storage and marks the "
        "metadata record as deleted. Only the owner or admin can delete."
    ),
    responses=API_RESPONSES,
)
async def delete_file(
    file_id: uuid.UUID,
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
    storage=Depends(get_storage),
) -> None:
    is_admin = user.role == "admin"
    await file_service.delete_file(
        db=db,
        storage=storage,
        file_id=file_id,
        requester_id=user.id,
        is_admin=is_admin,
    )
