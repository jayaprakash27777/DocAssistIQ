"""DocAssistIQ — File Object Service (Phase 11).

Handles secure file upload, download URL generation, and deletion.

Security rules enforced here:
  1. Server-generated object keys only — no user-supplied paths.
  2. File size limit: default 50 MB (configurable).
  3. Allowed MIME types whitelist — rejection on anything not in the list.
  4. Filename sanitisation — stored as metadata only, never used in key.
  5. Path traversal prevention — impossible by design (UUID key generation).
  6. File execution prevention — download via presigned URL (browser safe).
  7. Ownership verification — only owner or admin can download/delete.
  8. Audit log on every mutating operation.

MIME type validation:
  Server-side MIME detection is used where python-magic is available.
  If not available, falls back to client-supplied content-type with strict
  whitelist enforcement. Rejected files are never written to storage.
"""

from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import PurePosixPath

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.audit import AuditLog, FileObject
from app.storage import MinioStorageProvider

log = structlog.get_logger(__name__)

# ── Constants ────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

# Strict whitelist — only these MIME types may be uploaded
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    [
        # Documents
        "application/pdf",
        # Images (for lab reports, imaging)
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
        # Plain text
        "text/plain",
        # Spreadsheets (structured data only — not executable)
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        # DICOM medical imaging (Phase 11 foundation)
        "application/dicom",
    ]
)

# Allowed file extensions as a secondary guard
ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".txt", ".csv", ".xlsx", ".dcm"]
)

# Pattern for safe filename display (non-path characters only)
_SAFE_FILENAME_RE = re.compile(r"[^\w\s.\-]", flags=re.UNICODE)


# ── Helpers ──────────────────────────────────────────────────


def _sanitise_filename(raw: str) -> str:
    """Strip path separators and dangerous characters from display filename."""
    # Take only the basename — no directories
    name = PurePosixPath(raw).name
    name = name.replace("\\", "").replace("/", "")
    # Collapse anything non-alphanumeric except . and -
    name = _SAFE_FILENAME_RE.sub("_", name)
    return name[:260] or "upload"


def _generate_object_key(owner_id: uuid.UUID, extension: str) -> str:
    """
    Generate a server-controlled object key.

    Format: ``uploads/{owner_id}/{random_uuid}{ext}``
    The owner_id shard enables per-user lifecycle management.
    The random UUID prevents enumeration.
    """
    file_uuid = uuid.uuid4()
    ext = extension.lower().lstrip(".")
    return f"uploads/{owner_id}/{file_uuid}.{ext}"


def _detect_mime(data: bytes, client_mime: str) -> str:
    """
    Detect MIME type using python-magic if available.

    Falls back to client-supplied content-type (still whitelisted).
    """
    try:
        import magic  # type: ignore[import]

        detected = magic.from_buffer(data[:4096], mime=True)
        return detected
    except ImportError:
        return client_mime


def _validate_upload(
    data: bytes,
    filename: str,
    client_mime: str,
) -> tuple[str, str]:
    """
    Validate upload and return (sanitised_filename, detected_mime).

    Raises ValidationError on any violation.
    """
    # 1. Size check
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB.", code="FILE_TOO_LARGE")

    if len(data) == 0:
        raise ValidationError("File must not be empty.", code="FILE_EMPTY")

    # 2. Sanitise filename
    sanitised = _sanitise_filename(filename)

    # 3. Extension check
    suffix = PurePosixPath(sanitised).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Extension '{suffix}' is not permitted. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}", code="FILE_TYPE_NOT_ALLOWED"
        )

    # 4. MIME detection + whitelist
    detected_mime = _detect_mime(data, client_mime)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"MIME type '{detected_mime}' is not permitted.", code="MIME_TYPE_NOT_ALLOWED")

    return sanitised, detected_mime


# ── Service functions ─────────────────────────────────────────


async def upload_file(
    db: AsyncSession,
    storage: MinioStorageProvider,
    owner_id: uuid.UUID,
    data: bytes,
    filename: str,
    client_mime: str,
    linked_entity_type: str | None = None,
    linked_entity_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
) -> FileObject:
    """
    Validate, upload, and record a file.

    Returns the FileObject ORM row (status='ready').
    Raises ValidationError on size/MIME/extension violations.
    Never stores the object key derived from user input.
    """
    sanitised_name, detected_mime = _validate_upload(data, filename, client_mime)

    # Determine extension for key generation
    suffix = PurePosixPath(sanitised_name).suffix or ".bin"
    object_key = _generate_object_key(owner_id, suffix)

    # Upload to object storage
    upload_result = await storage.upload(
        data=data,
        object_key=object_key,
        mime_type=detected_mime,
    )

    # Persist metadata row
    file_obj = FileObject(
        owner_id=owner_id,
        tenant_id=tenant_id,
        object_key=object_key,
        original_filename=sanitised_name,
        mime_type=detected_mime,
        size_bytes=upload_result.size_bytes,
        checksum_sha256=upload_result.checksum_sha256,
        status="ready",
        scan_status="pending",  # Async scan in future phase
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
    )

    db.add(file_obj)
    db.add(
        AuditLog(
            actor_id=owner_id,
            action="file.uploaded",
            entity_type="file_object",
            entity_id=None,  # flushed after commit
            severity="info",
        )
    )
    await db.flush()

    # Update audit entity_id after flush
    file_obj_id = file_obj.id
    await db.refresh(file_obj)
    await db.commit()

    log.info(
        "file_uploaded",
        file_id=str(file_obj.id),
        owner_id=str(owner_id),
        mime=detected_mime,
        size=upload_result.size_bytes,
    )

    return file_obj


async def get_download_url(
    db: AsyncSession,
    storage: MinioStorageProvider,
    file_id: uuid.UUID,
    requester_id: uuid.UUID,
    is_admin: bool = False,
    expires_seconds: int = 3600,
) -> str:
    """
    Generate a presigned download URL for a file.

    Only the owner or an admin can download.
    Raises NotFoundError or AuthorizationError as appropriate.
    """
    result = await db.execute(select(FileObject).where(FileObject.id == file_id))
    file_obj = result.scalar_one_or_none()

    if file_obj is None or file_obj.status == "deleted":
        raise NotFoundError("File not found.", code="FILE_NOT_FOUND")

    if file_obj.status == "quarantined":
        raise ValidationError("This file has been quarantined and cannot be downloaded.", code="FILE_QUARANTINED")

    if not is_admin and file_obj.owner_id != requester_id:
        raise AuthorizationError("Access denied to this file.")

    url = storage.get_presigned_download_url(
        object_key=file_obj.object_key,
        expires_seconds=expires_seconds,
    )

    log.info(
        "file_download_url_generated",
        file_id=str(file_id),
        requester=str(requester_id),
        expires=expires_seconds,
    )

    return url


async def delete_file(
    db: AsyncSession,
    storage: MinioStorageProvider,
    file_id: uuid.UUID,
    requester_id: uuid.UUID,
    is_admin: bool = False,
) -> None:
    """
    Soft-delete the file metadata row and hard-delete from object storage.

    Only the owner or an admin can delete.
    """
    result = await db.execute(select(FileObject).where(FileObject.id == file_id))
    file_obj = result.scalar_one_or_none()

    if file_obj is None or file_obj.status == "deleted":
        raise NotFoundError("File not found.", code="FILE_NOT_FOUND")

    if not is_admin and file_obj.owner_id != requester_id:
        raise AuthorizationError("Access denied to this file.")

    # Hard-delete from object storage first
    await storage.delete(file_obj.object_key)

    # Soft-delete metadata
    file_obj.status = "deleted"
    db.add(
        AuditLog(
            actor_id=requester_id,
            action="file.deleted",
            entity_type="file_object",
            entity_id=file_obj.id,
            severity="info",
        )
    )
    await db.commit()

    log.info("file_deleted", file_id=str(file_id), requester=str(requester_id))


async def list_my_files(
    db: AsyncSession,
    owner_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[FileObject], int]:
    """Return paginated list of non-deleted files owned by owner_id."""
    offset = (page - 1) * page_size

    from sqlalchemy import func

    count_r = await db.execute(
        select(func.count())
        .select_from(FileObject)
        .where(FileObject.owner_id == owner_id, FileObject.status != "deleted")
    )
    total = count_r.scalar_one()

    result = await db.execute(
        select(FileObject)
        .where(FileObject.owner_id == owner_id, FileObject.status != "deleted")
        .order_by(FileObject.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    files = list(result.scalars().all())

    return files, total
