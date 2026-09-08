"""DocAssistIQ — Medical Knowledge Entity Models.

Symptom, Disease, Investigation, Medicine — the core medical knowledge
domain. These are REFERENCE data entities (not patient-specific).

CRITICAL CLINICAL SAFETY REQUIREMENT:
  All content in these tables MUST carry a source provenance reference
  (source_id FK to Source) and a knowledge_version_id.
  Content MUST NOT be fabricated or hardcoded.
  All AI-generated content MUST be labelled is_ai_generated=True
  and MUST be reviewed by a clinician before entering 'verified' status.

Many-to-many relationships:
  Symptom ↔ Disease : DiseaseSymptom join table
  Disease ↔ Investigation : DiseaseInvestigation join table
  Disease ↔ Medicine : DiseaseMedicine join table (treatment associations)
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base

from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeVersioningMixin:
    """Fields to track knowledge quality and versioning (Phase 15)."""
    
    publication_date: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Original publication date of the source"
    )
    retrieval_date: Mapped[str | None] = mapped_column(
        String(40), nullable=True, comment="When it was ingested"
    )
    effective_date: Mapped[str | None] = mapped_column(
        String(40), nullable=True, comment="When this became active in production"
    )
    version_string: Mapped[str | None] = mapped_column(
        String(40), nullable=True, comment="Semantic version or source version"
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="Hash of the core content to detect mutations"
    )
    credibility_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="unknown", comment="'primary' | 'secondary' | 'tertiary' | 'unknown'"
    )
    evidence_level: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="Highest level of evidence (e.g. 'Ia')"
    )
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, comment="FK to the entity that superseded this one"
    )


# ── Symptom ───────────────────────────────────────────────────


class Symptom(KnowledgeVersioningMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A medical symptom in the knowledge base."""

    __tablename__ = "symptoms"

    __table_args__ = (
        Index("ix_symptoms_code", "code", unique=True),
        Index("ix_symptoms_status", "status"),
    )

    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        comment="Canonical code (e.g. SNOMED CT concept ID or internal slug)",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable symptom name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Clinical description — sourced from verified reference only",
    )

    icd10_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Optional ICD-10 code mapping",
    )

    snomed_id: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="Optional SNOMED CT concept ID",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="PENDING_REVIEW",
        comment="'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED' | 'OUTDATED'",
    )

    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True if content was AI-generated (requires clinician review)",
    )

    knowledge_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_versions.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to the knowledge version when this record was created/updated",
    )

    def __repr__(self) -> str:
        return f"<Symptom code={self.code!r} status={self.status!r}>"


# ── Disease ───────────────────────────────────────────────────


class Disease(KnowledgeVersioningMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A disease or condition in the knowledge base."""

    __tablename__ = "diseases"

    __table_args__ = (
        Index("ix_diseases_code", "code", unique=True),
        Index("ix_diseases_status", "status"),
    )

    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        comment="Canonical code (internal slug or ICD-10)",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable disease name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Clinical description — sourced from verified reference only",
    )

    icd10_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="ICD-10 code",
    )

    icd11_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="ICD-11 code",
    )

    snomed_id: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="SNOMED CT concept ID",
    )

    category: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        comment="Clinical category (e.g. 'infectious', 'cardiovascular')",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="PENDING_REVIEW",
        comment="'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED' | 'OUTDATED'",
    )

    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    knowledge_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Disease code={self.code!r} status={self.status!r}>"


# ── Investigation ─────────────────────────────────────────────


class Investigation(KnowledgeVersioningMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A medical investigation (test, imaging, procedure) in the knowledge base."""

    __tablename__ = "investigations"

    __table_args__ = (
        Index("ix_investigations_code", "code", unique=True),
    )

    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        comment="Canonical code (LOINC, SNOMED, or internal slug)",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Clinical description — sourced from verified reference only",
    )

    loinc_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="LOINC code if applicable",
    )

    investigation_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default="laboratory",
        comment="'laboratory' | 'imaging' | 'procedure' | 'questionnaire'",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="PENDING_REVIEW",
        comment="'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED' | 'OUTDATED'",
    )

    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    knowledge_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Investigation code={self.code!r}>"


# ── Medicine ──────────────────────────────────────────────────


class Medicine(KnowledgeVersioningMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A medicinal product in the knowledge base.

    MANDATORY: All medication information displayed to clinicians MUST carry
    the label 'REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED'.
    Content sourced from verified pharmacological references only.
    No dosage, interaction, or contraindication data is fabricated.
    """

    __tablename__ = "medicines"

    __table_args__ = (
        Index("ix_medicines_code", "code", unique=True),
    )

    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        comment="Internal slug or RxNorm CUI",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Generic (INN) name",
    )

    brand_names: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated brand names (informational only)",
    )

    atc_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="WHO ATC classification code",
    )

    rxnorm_cui: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="RxNorm Concept Unique Identifier",
    )

    drug_class: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        comment="Pharmacological class",
    )

    mechanism_of_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Brief mechanism of action (reference only; clinician review required)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="PENDING_REVIEW",
        comment="'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED' | 'OUTDATED'",
    )

    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    knowledge_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Medicine code={self.code!r} name={self.name!r}>"


# ── Many-to-many join tables ──────────────────────────────────


class DiseaseSymptom(Base):
    """Join table: Disease ↔ Symptom with clinical metadata."""

    __tablename__ = "disease_symptoms"

    __table_args__ = (
        UniqueConstraint("disease_id", "symptom_id", name="uq_disease_symptom"),
    )

    disease_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        primary_key=True,
    )

    symptom_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("symptoms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    frequency: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="'very_common' | 'common' | 'uncommon' | 'rare' | 'very_rare'",
    )

    specificity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Diagnostic specificity [0.0–1.0] from literature (reference only)",
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        comment="Source from which this association was derived",
    )


class DiseaseInvestigation(Base):
    """Join table: Disease ↔ Investigation."""

    __tablename__ = "disease_investigations"

    __table_args__ = (
        UniqueConstraint("disease_id", "investigation_id", name="uq_disease_investigation"),
    )

    disease_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        primary_key=True,
    )

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        primary_key=True,
    )

    indication: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        comment="'diagnostic' | 'monitoring' | 'screening'",
    )

    priority: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="'first_line' | 'second_line' | 'adjunct'",
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )


class DiseaseMedicine(Base):
    """Join table: Disease ↔ Medicine (treatment associations)."""

    __tablename__ = "disease_medicines"

    __table_args__ = (
        UniqueConstraint("disease_id", "medicine_id", name="uq_disease_medicine"),
    )

    disease_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="CASCADE"),
        primary_key=True,
    )

    medicine_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("medicines.id", ondelete="CASCADE"),
        primary_key=True,
    )

    treatment_role: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="'first_line' | 'second_line' | 'adjunct' | 'prophylaxis'",
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )
