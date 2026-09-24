"""DocAssistIQ — PatientProfile Model.

Represents a de-identified patient profile.
Strict clinical safety rules apply: this model stores ONLY pseudo-demographics
(age_group, biological_sex) and clinical baselines. It must NEVER store
real PII such as Name, DOB, MRN, or address.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class PatientProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A de-identified patient profile.
    Links PatientSessions together chronologically without violating PII constraints.
    """

    __tablename__ = "patient_profiles"

    __table_args__ = (
        Index("ix_patient_profiles_tenant", "tenant_id"),
        UniqueConstraint("tenant_id", "patient_ref", name="uq_tenant_patient_ref"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Owning tenant",
    )

    patient_ref: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment=(
            "Opaque external reference from EMR/HIS. "
            "NOT a real name, NHS number, or any direct identifier."
        ),
    )

    age_group: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Pseudo-demographic: e.g., '18-25', '60-70'",
    )

    biological_sex: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Biological sex: 'male', 'female', 'other', 'unknown'",
    )

    baseline_conditions: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        server_default="{}",
        comment="JSON containing known past medical history / chronic conditions",
    )

    sessions: Mapped[list["PatientSession"]] = relationship(  # type: ignore
        "PatientSession",
        back_populates="patient_profile",
        cascade="all, delete-orphan",
        order_by="PatientSession.created_at",
    )

    def __repr__(self) -> str:
        return f"<PatientProfile id={self.id} patient_ref={self.patient_ref!r}>"
