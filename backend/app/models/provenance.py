"""DocAssistIQ — Source, Evidence, Article, KnowledgeVersion Models.

Provenance and knowledge versioning layer.

Source: a registered medical information source (e.g. PubMed, RxNorm,
  WHO Guidelines). Registered manually by admins — never fabricated.

Evidence: a specific piece of evidence (association) linking a clinical
  claim to a source article/guideline with explicit strength and grade.

Article: an individual published article or guideline document from a
  Source, with DOI/PMID and retrieval metadata.

KnowledgeVersion: a snapshot version tag applied to all knowledge content
  at a point in time, enabling rollback and audit of knowledge base changes.

CLINICAL SAFETY:
  - No clinical evidence is fabricated or hardcoded.
  - All associations between entities and their evidence must trace to a
    registered Source with real access/licensing metadata.
  - evidence_grade follows standard EBM grading (Ia/Ib/IIa/IIb/III/IV).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A versioned snapshot of the knowledge base."""

    __tablename__ = "knowledge_versions"

    __table_args__ = (
        Index("ix_knowledge_versions_tag", "tag", unique=True),
    )

    tag: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        unique=True,
        comment="Semantic version tag (e.g. '2026.09.1') — globally unique",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Summary of changes in this knowledge version",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="draft",
        comment="'draft' | 'published' | 'archived'",
    )

    published_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin who published this version",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeVersion tag={self.tag!r} status={self.status!r}>"


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A registered medical information source.

    Admins register real sources with verified licensing information.
    Content must not be ingested from unregistered or unlicensed sources.
    """

    __tablename__ = "sources"

    __table_args__ = (
        Index("ix_sources_code", "code", unique=True),
    )

    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        comment="Internal unique code (e.g. 'pubmed', 'rxnorm', 'who_guidelines')",
    )

    organisation: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Publishing organisation (e.g. 'NIH / NLM', 'WHO')",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Source name (e.g. 'PubMed Central', 'RxNorm')",
    )

    base_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Base URL or API endpoint",
    )

    access_mechanism: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        server_default="api",
        comment="'api' | 'bulk_download' | 'manual' | 'licensed_feed'",
    )

    data_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        comment="'literature' | 'drug_database' | 'clinical_guidelines' | 'coding_system'",
    )

    license_info: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="License / access terms (must be verified before ingestion)",
    )

    is_production_suitable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True only after licensing and quality review by admin",
    )

    last_verified_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="ISO-8601 date when access/licensing was last confirmed",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="registered",
        comment="'registered' | 'active' | 'suspended' | 'retired'",
    )

    def __repr__(self) -> str:
        return f"<Source code={self.code!r} status={self.status!r}>"


class Article(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A published article or guideline document from a Source."""

    __tablename__ = "articles"

    __table_args__ = (
        Index("ix_articles_source", "source_id"),
        Index("ix_articles_doi", "doi"),
        Index("ix_articles_pmid", "pmid"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Origin source",
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Article or guideline title",
    )

    authors: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Author list (plain text, not structured)",
    )

    doi: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Digital Object Identifier",
    )

    pmid: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="PubMed ID",
    )

    published_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="ISO-8601 publication date (YYYY-MM-DD or YYYY-MM)",
    )

    journal: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="Journal or guideline body name",
    )

    abstract: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Abstract or summary (sourced verbatim — do not paraphrase or fabricate)",
    )

    url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL for full-text access",
    )

    retrieval_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="indexed",
        comment="'indexed' | 'full_text' | 'unavailable'",
    )

    def __repr__(self) -> str:
        return f"<Article id={self.id} doi={self.doi!r}>"


class Evidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A specific piece of evidence linking a clinical entity to a source.

    Traces the provenance of a clinical claim (e.g. Disease→Symptom
    association) to a specific article or guideline, with evidence grade
    following standard EBM (Evidence-Based Medicine) hierarchy.

    evidence_grade: Ia | Ib | IIa | IIb | III | IV
    recommendation_grade: A | B | C | D | GPP
    """

    __tablename__ = "evidence"

    __table_args__ = (
        Index("ix_evidence_article", "article_id"),
        Index("ix_evidence_entity", "entity_type", "entity_id"),
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Supporting article or guideline",
    )

    # Polymorphic entity reference (disease, symptom, investigation, medicine)
    entity_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="'disease' | 'symptom' | 'investigation' | 'medicine'",
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of the referenced entity (no FK — polymorphic)",
    )

    claim: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The specific clinical claim this evidence supports",
    )

    evidence_grade: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        comment="EBM grade: Ia | Ib | IIa | IIb | III | IV",
    )

    recommendation_grade: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        comment="Recommendation grade: A | B | C | D | GPP",
    )

    is_ai_extracted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True if evidence was extracted by AI (requires expert review)",
    )

    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Expert who reviewed AI-extracted evidence",
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence id={self.id} entity={self.entity_type}/{self.entity_id} "
            f"grade={self.evidence_grade!r}>"
        )
