"""DocAssistIQ — Role and Permission Models.

Fine-grained RBAC layer on top of the coarse ``user.role`` field.

Design:
  Role        — named set of permissions (e.g. "senior_doctor", "resident")
  Permission  — atomic capability string (e.g. "consultation:create")
  RolePermission — join table (many-to-many: Role ↔ Permission)
  UserRole    — join table (many-to-many: User ↔ Role, tenant-scoped)

The existing ``user.role`` field ('doctor' | 'admin') remains the primary
gate for Phase 5 RBAC. This model extends it for fine-grained control
without breaking existing guards.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A named bundle of permissions within a tenant."""

    __tablename__ = "roles"

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owning tenant (roles are tenant-scoped)",
    )

    name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="Role name (unique per tenant, e.g. 'senior_doctor')",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of this role",
    )

    is_system: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="false",
        comment="True for built-in roles that cannot be deleted",
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An atomic capability string (e.g. 'consultation:create')."""

    __tablename__ = "permissions"

    __table_args__ = (
        Index("ix_permissions_code", "code", unique=True),
    )

    code: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
        comment="Machine-readable capability code, globally unique",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of this capability",
    )

    resource: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        comment="Resource domain (e.g. 'consultation', 'patient_session')",
    )

    action: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="Action (e.g. 'create', 'read', 'update', 'delete')",
    )

    def __repr__(self) -> str:
        return f"<Permission code={self.code!r}>"


class RolePermission(Base):
    """Join table: Role ↔ Permission (many-to-many)."""

    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to role",
    )

    permission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to permission",
    )


class UserRole(Base):
    """Join table: User ↔ Role, scoped to a tenant."""

    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "tenant_id", name="uq_user_roles"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to user",
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to role",
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="Tenant scope for this assignment",
    )
