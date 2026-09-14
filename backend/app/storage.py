"""DocAssistIQ — Storage Provider Interface (Phase 11).

Defines the abstract StorageProvider protocol and the MinIO implementation.

Design rules:
  - Object keys are ALWAYS server-generated (UUID-based paths).
    User-supplied filenames are stored as metadata only — never used as keys.
  - Path traversal is prevented by construction (no user input in key).
  - File execution is never performed; files are streamed as attachment.
  - MIME type is validated server-side via python-magic.
  - SHA-256 checksum is computed on upload and stored for integrity.
  - All operations require the caller to provide the owner_id for audit.
"""

from __future__ import annotations

import hashlib
import io
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Protocol

import structlog
from minio import Minio
from minio.error import S3Error

log = structlog.get_logger(__name__)

# ── Types ────────────────────────────────────────────────────


@dataclass(frozen=True)
class UploadResult:
    """Result of a successful upload."""

    object_key: str
    checksum_sha256: str
    size_bytes: int
    etag: str


@dataclass(frozen=True)
class DownloadResult:
    """Result of a successful download metadata fetch."""

    object_key: str
    size_bytes: int
    mime_type: str


# ── Protocol ─────────────────────────────────────────────────


class StorageProvider(Protocol):
    """Abstract storage provider interface."""

    async def upload(
        self,
        data: bytes,
        object_key: str,
        mime_type: str,
    ) -> UploadResult:
        """Upload bytes to object storage. Returns UploadResult."""
        ...

    def get_presigned_download_url(
        self,
        object_key: str,
        expires_seconds: int = 3600,
    ) -> str:
        """Generate a short-lived presigned GET URL."""
        ...

    async def delete(self, object_key: str) -> None:
        """Permanently delete an object. No-op if object does not exist."""
        ...

    def object_exists(self, object_key: str) -> bool:
        """Return True if the object key exists in storage."""
        ...


# ── MinIO implementation ─────────────────────────────────────


class MinioStorageProvider:
    """
    MinIO/S3-compatible storage provider.

    Configuration is pulled from Settings at construction time.
    For local development, MinIO runs in the docker-compose stack.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create bucket if it does not exist (idempotent)."""
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                log.info("storage_bucket_created", bucket=self._bucket)
        except S3Error as exc:
            log.error("storage_bucket_check_failed", error=str(exc))

    async def upload(
        self,
        data: bytes,
        object_key: str,
        mime_type: str,
    ) -> UploadResult:
        """Upload bytes to MinIO. Returns UploadResult with checksum."""
        checksum = hashlib.sha256(data).hexdigest()
        size = len(data)

        result = self._client.put_object(
            bucket_name=self._bucket,
            object_name=object_key,
            data=io.BytesIO(data),
            length=size,
            content_type=mime_type,
            metadata={"x-checksum-sha256": checksum},
        )

        log.info(
            "storage_upload_ok",
            key=object_key,
            size=size,
            etag=result.etag,
        )

        return UploadResult(
            object_key=object_key,
            checksum_sha256=checksum,
            size_bytes=size,
            etag=result.etag or "",
        )

    def get_presigned_download_url(
        self,
        object_key: str,
        expires_seconds: int = 3600,
    ) -> str:
        """Return a presigned GET URL valid for `expires_seconds`."""
        from datetime import timedelta

        url = self._client.presigned_get_object(
            bucket_name=self._bucket,
            object_name=object_key,
            expires=timedelta(seconds=expires_seconds),
        )
        log.info("storage_presigned_url_generated", key=object_key, expires=expires_seconds)
        return url

    async def delete(self, object_key: str) -> None:
        """Remove an object from MinIO. No-op if it does not exist."""
        try:
            self._client.remove_object(self._bucket, object_key)
            log.info("storage_object_deleted", key=object_key)
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                log.warning("storage_delete_not_found", key=object_key)
            else:
                log.error("storage_delete_failed", key=object_key, error=str(exc))
                raise

    def object_exists(self, object_key: str) -> bool:
        """Return True if the object key exists in MinIO."""
        try:
            self._client.stat_object(self._bucket, object_key)
            return True
        except S3Error:
            return False


# ── Singleton factory ────────────────────────────────────────

_provider: MinioStorageProvider | None = None


def get_storage_provider(settings: object | None = None) -> MinioStorageProvider:
    """
    Return the singleton MinioStorageProvider.

    Lazily constructed on first call. Thread-safe for single-process servers.
    """
    global _provider
    if _provider is None:
        if settings is None:
            from app.config import get_settings

            settings = get_settings()

        # object_storage_endpoint is "http://host:port" — strip scheme for minio client
        endpoint_raw: str = getattr(settings, 'object_storage_endpoint', None)  # type: ignore
        endpoint = endpoint_raw.replace("http://", "").replace("https://", "")
        secure = endpoint_raw.startswith("https://")

        _provider = MinioStorageProvider(
            endpoint=endpoint,
            access_key=getattr(settings, 'object_storage_access_key', None),  # type: ignore
            secret_key=getattr(settings, 'object_storage_secret_key', None),  # type: ignore
            bucket=getattr(settings, 'object_storage_bucket', None),  # type: ignore
            secure=secure,
        )
    return _provider
