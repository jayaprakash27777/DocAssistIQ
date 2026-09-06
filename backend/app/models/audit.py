"""DocAssistIQ — AuditLog, Feedback, FileObject Models.

AuditLog: immutable append-only record of all state-changing operations.
  Used for compliance, forensics, and clinical audit trails.
  Records are never deleted; archival is handled by retention policy.

Feedback: clinician feedback on AI-generated suggestions.
  Used to improve model quality; stored separately from clinical record.
  Never used to change clinical state automatically.

FileObject: metadata record for uploaded files stored in object storage.
  No file content is stored in the database. The object_key references
  the object storage location.
  File execution is prohibited (enforced at the API layer).
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """
    Immutable append-only audit trail for all state-changing operations.

    Records are write-once; no UPDATE or DELETE is permitted after creation
    (enforced at the service layer, not the database constraint).
    The ``action`` field uses past-tense verb notation: 'user.created',
    'consultation.submitted', 'finding.confirmed', etc.
    """

    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("ix_audit_logs_actor", "actor_id"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_tenant", "tenant_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    # Append-only timestamp — no updated_at
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this audit event was recorded",
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        comment="Tenant context (null for system-level events)",
    )

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the action (null for automated/system actions)",
    )

    action: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        comment="Past-tense verb (e.g. 'consultation.submitted', 'finding.confirmed')",
    )

    entity_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        comment="Type of entity affected (e.g. 'consultation', 'clinical_note')",
    )

    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the affected entity (null for non-entity events)",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IPv4 or IPv6 address of the requestor",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="HTTP User-Agent header of the requestor",
    )

    request_id: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="X-Request-ID for correlation with access logs",
    )

    diff: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON diff of changed fields (old/new) — no PII",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="info",
        comment="'info' | 'warning' | 'critical'",
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r}>"


class Feedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Clinician feedback on AI-generated suggestions.

    Stored for model quality improvement only. Feedback data is NEVER
    used to automatically change clinical findings or consultation state.
    """

    __tablename__ = "feedback"

    __table_args__ = (
        Index("ix_feedback_consultation", "consultation_id"),
        Index("ix_feedback_clinician", "clinician_id"),
    )

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Consultation this feedback relates to",
    )

    clinician_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Clinician providing feedback",
    )

    target_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="'finding' | 'investigation' | 'medicine' | 'overall'",
    )

    target_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the specific AI suggestion being rated (null for overall)",
    )

    rating: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="1–5 Likert rating (null if free-text only)",
    )

    is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Binary correct/incorrect assessment (null if not applicable)",
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text feedback (non-PII)",
    )

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} target={self.target_type!r} rating={self.rating}>"


class FileObject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Metadata record for a file stored in object storage.

    IMPORTANT:
      - No file content is stored in the database.
      - object_key is generated server-side (never user-controlled paths).
      - File execution at serve time is prohibited.
      - Access is controlled by owner_id and tenant_id.
      - Virus/malware scanning is tracked via scan_status.
    """

    __tablename__ = "file_objects"

    __table_args__ = (
        Index("ix_file_objects_owner", "owner_id"),
        Index("ix_file_objects_tenant", "tenant_id"),
        Index("ix_file_objects_key", "object_key", unique=True),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who uploaded this file",
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        comment="Tenant scope",
    )

    object_key: Mapped[str] = mapped_column(
        String(400),
        nullable=False,
        unique=True,
        comment="Server-generated object storage key (not user-supplied path)",
    )

    original_filename: Mapped[str] = mapped_column(
        String(260),
        nullable=False,
        comment="Original filename as supplied by the client (display only)",
    )

    mime_type: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        comment="Server-verified MIME type (not trusted from client)",
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="File size in bytes",
    )

    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hex digest of file contents",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="'pending' | 'ready' | 'quarantined' | 'deleted'",
    )

    scan_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Virus scan status: 'pending' | 'clean' | 'infected' | 'failed'",
    )

    retention_until: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="ISO-8601 retention date; null = indefinite",
    )

    linked_entity_type: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
        comment="Entity type this file is attached to (polymorphic)",
    )

    linked_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the entity this file is attached to",
    )

    def __repr__(self) -> str:
        return f"<FileObject id={self.id} key={self.object_key!r} status={self.status!r}>"
