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
    poll_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    poll_options: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False, server_default="[]")
    is_urgent: Mapped[bool] = mapped_column(default=False, server_default="false")
    patient_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_solved: Mapped[bool] = mapped_column(default=False, server_default="false")
    outcome_reported_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quoted_post_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctor_posts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    attachments: Mapped[list["PostAttachment"]] = relationship("PostAttachment", back_populates="post", cascade="all, delete-orphan")
    likes: Mapped[list["PostLike"]] = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["PostComment"]] = relationship("PostComment", back_populates="post", cascade="all, delete-orphan", order_by="PostComment.created_at")
    bookmarks: Mapped[list["PostBookmark"]] = relationship("PostBookmark", back_populates="post", cascade="all, delete-orphan")
    treatment_suggestions: Mapped[list["PostTreatmentSuggestion"]] = relationship(
        "PostTreatmentSuggestion", back_populates="post", cascade="all, delete-orphan", order_by="PostTreatmentSuggestion.created_at"
    )


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
    """Likes/reactions on a doctor post by other verified doctors."""
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
    reaction_type: Mapped[str | None] = mapped_column(String(50), default="validate", server_default="validate")

    post: Mapped["DoctorPost"] = relationship("DoctorPost", back_populates="likes")

class PostPollVote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Real consensus votes cast by verified doctors on clinical dilemma polls."""
    __tablename__ = "post_poll_votes"
    __table_args__ = (UniqueConstraint("post_id", "doctor_id", name="uq_post_poll_vote_doctor"),)

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
    option_index: Mapped[int] = mapped_column(nullable=False)

class PostEndorsement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Real endorsements / citations given by verified doctors to clinical cases."""
    __tablename__ = "post_endorsements"
    __table_args__ = (UniqueConstraint("post_id", "doctor_id", name="uq_post_endorsement_doctor"),)

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

class PostTreatmentSuggestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Structured clinical treatment suggestions submitted by peer verified doctors."""
    __tablename__ = "post_treatment_suggestions"

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
    drug_or_intervention: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage_and_route: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clinical_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_grade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    endorsements_count: Mapped[int] = mapped_column(default=0, server_default="0")
    is_adopted: Mapped[bool] = mapped_column(default=False, server_default="false")

    post: Mapped["DoctorPost"] = relationship("DoctorPost", back_populates="treatment_suggestions")

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
    folder_name: Mapped[str] = mapped_column(String(100), default="General", server_default="General")

    post: Mapped["DoctorPost"] = relationship("DoctorPost", back_populates="bookmarks")

class DoctorFollow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Real follow relationships between verified doctors."""
    __tablename__ = "doctor_follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_doctor_follow"),)

    follower_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

class CurbsideMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Secure doctor-to-doctor curbside direct consultation linked to a clinical case."""
    __tablename__ = "curbside_messages"

    post_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctor_posts.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="routine", server_default="routine")
    is_read: Mapped[bool] = mapped_column(default=False, server_default="false")


class DoctorCircle(Base):
    """Specialty medical communities and doctor circles."""
    __tablename__ = "doctor_circles"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(20), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list)


class DoctorCircleMember(Base):
    """Physician membership in doctor circles."""
    __tablename__ = "doctor_circle_members"
    __table_args__ = (UniqueConstraint("circle_id", "doctor_id", name="uq_doctor_circle_member"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circle_id: Mapped[str] = mapped_column(String(100), ForeignKey("doctor_circles.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)


class CMEEvent(Base):
    """Accredited Continuing Medical Education and Grand Rounds events."""
    __tablename__ = "cme_events"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    date_str: Mapped[str] = mapped_column(String(100), nullable=False)
    time_str: Mapped[str] = mapped_column(String(100), nullable=False)
    speaker: Mapped[str] = mapped_column(String(255), nullable=False)
    speaker_title: Mapped[str] = mapped_column(String(255), nullable=False)
    cme_credits: Mapped[float] = mapped_column(default=1.0)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    topics: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list)


class CMEEventRSVP(Base):
    """Doctor RSVPs to accredited CME Grand Rounds sessions."""
    __tablename__ = "cme_event_rsvps"
    __table_args__ = (UniqueConstraint("event_id", "doctor_id", name="uq_cme_event_rsvp"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(100), ForeignKey("cme_events.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)



