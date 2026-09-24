"""DocAssistIQ - Social Hub Models for Verified Doctors."""

import uuid
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin

class DoctorPost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A structured clinical post shared by a verified doctor on the social hub."""
    __tablename__ = "doctor_posts"

    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Structured Clinical Data
    disease_name: Mapped[str] = mapped_column(String(255), nullable=False)
    clinical_findings: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    treatment_plan: Mapped[str] = mapped_column(Text, nullable=False)
    drugs_used: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False, server_default="[]")
    specialty_tags: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False, server_default="[]")

    # Relationships
    attachments: Mapped[list["PostAttachment"]] = relationship("PostAttachment", back_populates="post", cascade="all, delete-orphan")
    likes: Mapped[list["PostLike"]] = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["PostComment"]] = relationship("PostComment", back_populates="post", cascade="all, delete-orphan", order_by="PostComment.created_at")
    bookmarks: Mapped[list["PostBookmark"]] = relationship("PostBookmark", back_populates="post", cascade="all, delete-orphan")

class PostAttachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """File attachments (e.g., X-rays, CT Scans) linked to a doctor post."""
    __tablename__ = "post_attachments"

    post_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctor_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)

    post: Mapped["DoctorPost"] = relationship("DoctorPost", back_populates="attachments")

class PostLike(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Likes on a doctor post by other verified doctors."""
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "doctor_id", name="uq_post_like_doctor"),)

    post_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctor_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    post: Mapped["DoctorPost"] = relationship("DoctorPost", back_populates="likes")

class PostComment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Comments on a doctor post by other verified doctors."""
    __tablename__ = "post_comments"

    post_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctor_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    post: Mapped["DoctorPost"] = relationship("DoctorPost", back_populates="comments")

class PostBookmark(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Bookmarks on a doctor post by other verified doctors for later review."""
    __tablename__ = "post_bookmarks"
    __table_args__ = (UniqueConstraint("post_id", "doctor_id", name="uq_post_bookmark_doctor"),)

    post_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctor_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    post: Mapped["DoctorPost"] = relationship("DoctorPost", back_populates="bookmarks")
