"""DocAssistIQ — Retention Service.

Implements automated configurable retention policies and explicit deletion protocols.
Handles scheduled purge of data older than retention limits (clinical data, audit logs)
and enforces deletion from object storage along with database deletion.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.infrastructure.storage import get_s3_client
from app.models.consultation import Consultation
from app.models.audit import AuditLog, FileObject

logger = structlog.get_logger(__name__)


async def purge_expired_data(db: AsyncSession, storage: Any, settings: Settings) -> dict[str, int]:
    """
    Identifies and permanently deletes records that have exceeded their retention period.
    Also ensures linked object storage files are deleted.

    Returns:
        A dictionary containing the count of deleted items per category.
    """
    now = datetime.now(timezone.utc)
    
    # 1. Calculate cutoff dates
    clinical_cutoff = now - timedelta(days=settings.retention_days_clinical)
    audit_cutoff = now - timedelta(days=settings.retention_days_audit)
    
    stats = {
        "consultations_deleted": 0,
        "files_deleted_db": 0,
        "files_deleted_storage": 0,
        "audit_logs_deleted": 0,
    }

    # 2. Find expired Consultations
    # Note: Consultations use `created_at`.
    stmt = select(Consultation.id).where(Consultation.created_at < clinical_cutoff)
    result = await db.execute(stmt)
    expired_consultation_ids = list(result.scalars().all())

    if expired_consultation_ids:
        # Find all associated files (linked_entity_type = 'consultation' and linked_entity_id in ids)
        file_stmt = select(FileObject).where(
            FileObject.linked_entity_type == "consultation",
            FileObject.linked_entity_id.in_(expired_consultation_ids)
        )
        file_result = await db.execute(file_stmt)
        expired_files = file_result.scalars().all()

        # Delete from object storage
        for f in expired_files:
            try:
                await storage.delete_object(f.object_key)
                stats["files_deleted_storage"] += 1
            except Exception as e:
                logger.error("storage_deletion_failed", object_key=f.object_key, error=str(e))
                # Even if storage delete fails (maybe already deleted), we proceed to remove the DB record
        
        # Delete files from DB
        if expired_files:
            delete_files_stmt = delete(FileObject).where(
                FileObject.id.in_([f.id for f in expired_files])
            )
            await db.execute(delete_files_stmt)
            stats["files_deleted_db"] = len(expired_files)

        # Delete the consultations (CASCADE will handle children like ClinicalNote, etc. if configured properly)
        delete_consultations_stmt = delete(Consultation).where(
            Consultation.id.in_(expired_consultation_ids)
        )
        res = await db.execute(delete_consultations_stmt)
        stats["consultations_deleted"] = res.rowcount  # type: ignore[attr-defined]

    # 3. Find and delete expired AuditLogs
    audit_stmt = delete(AuditLog).where(AuditLog.created_at < audit_cutoff)
    audit_res = await db.execute(audit_stmt)
    stats["audit_logs_deleted"] = audit_res.rowcount  # type: ignore[attr-defined]  # type: ignore[attr-defined]

    # Commit the transaction
    await db.commit()
    
    logger.info("retention_purge_completed", stats=stats)
    return stats
