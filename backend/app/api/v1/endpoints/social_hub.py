"""DocAssistIQ — Social Hub API v2 (Twitter/LinkedIn Style Upgrade).

New endpoints:
  GET  /hub/feed             — Main social feed with pagination (enhanced)
  POST /hub/posts            — Create structured clinical post
  POST /hub/posts/{id}/like  — Toggle like + triggers credibility refresh
  POST /hub/posts/{id}/bookmark — Toggle bookmark
  POST /hub/posts/{id}/comments — Add peer-review comment
  GET  /hub/posts/{id}/comments — Get paginated comment thread
  GET  /hub/trending         — Trending diseases + hashtags
  GET  /hub/stories          — Top 5 posts from last 24h (engagement-sorted)
  GET  /hub/explore          — Doctors by specialty with post counts
  GET  /hub/hashtags         — Top hashtags with post counts
  GET  /hub/search           — Full-text search across posts
  GET  /hub/profiles/{id}/posts — Posts for a specific doctor
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_

from app.dependencies import get_db
from app.authorization import get_current_doctor_profile
from app.models.doctor import Doctor
from app.models.audit import FileObject
from app.models.social import DoctorPost, PostLike, PostComment, PostAttachment, PostBookmark
from app.schemas.social import (
    DoctorPostCreate, DoctorPostResponse,
    PostCommentCreate, PostCommentResponse
)
from app.api.v1.endpoints.ws import manager
from app.services.ingestion.social_ingester import ingest_doctor_post, refresh_post_credibility
from app.infrastructure.database import get_session_factory

router = APIRouter()


# ─── Background Task Helpers ───────────────────────────────────────────────────

async def _trigger_ingestion(post_id: uuid.UUID):
    async with get_session_factory()() as db:
        post = await db.scalar(select(DoctorPost).where(DoctorPost.id == post_id))
        if post:
            await ingest_doctor_post(db, post)


async def _trigger_credibility_refresh(post_id: uuid.UUID):
    async with get_session_factory()() as db:
        await refresh_post_credibility(db, post_id)


# ─── Feed ──────────────────────────────────────────────────────────────────────

async def _enrich_post(post: DoctorPost, db: AsyncSession, doctor: Doctor) -> DoctorPostResponse:
    """Enrich a post with engagement counts, like/bookmark status, and top comments."""
    likes_count = await db.scalar(select(func.count(PostLike.id)).where(PostLike.post_id == post.id)) or 0
    comments_count = await db.scalar(select(func.count(PostComment.id)).where(PostComment.post_id == post.id)) or 0
    is_liked = await db.scalar(select(PostLike).where(PostLike.post_id == post.id, PostLike.doctor_id == doctor.id))
    is_bookmarked = await db.scalar(select(PostBookmark).where(PostBookmark.post_id == post.id, PostBookmark.doctor_id == doctor.id))
    comments = await db.scalars(
        select(PostComment).where(PostComment.post_id == post.id)
        .order_by(PostComment.created_at.desc()).limit(3)
    )

    resp = DoctorPostResponse.model_validate(post)
    resp.likes_count = likes_count
    resp.comments_count = comments_count
    resp.is_liked_by_me = bool(is_liked)
    resp.is_bookmarked_by_me = bool(is_bookmarked)
    resp.comments = [PostCommentResponse.model_validate(c) for c in comments]
    return resp


@router.get("/feed", response_model=List[DoctorPostResponse])
async def get_social_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    disease: Optional[str] = None,
    specialty: Optional[str] = None,
    sort_by: str = Query("recent", enum=["recent", "trending"]),
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Get the social timeline of verified doctor posts with filtering and sorting."""
    stmt = select(DoctorPost).offset(skip).limit(limit)

    if disease:
        stmt = stmt.where(DoctorPost.disease_name.ilike(f"%{disease}%"))
    if specialty:
        stmt = stmt.where(DoctorPost.specialty_tags.contains([specialty]))

    if sort_by == "trending":
        # Trending = high engagement in last 7 days
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        stmt = stmt.where(DoctorPost.created_at >= week_ago)
        # We approximate trending by newest for now (join for count would be expensive)
        stmt = stmt.order_by(desc(DoctorPost.created_at))
    else:
        stmt = stmt.order_by(desc(DoctorPost.created_at))

    result = await db.execute(stmt)
    posts = result.scalars().unique().all()

    return [await _enrich_post(p, db, doctor) for p in posts]


# ─── Trending ──────────────────────────────────────────────────────────────────

@router.get("/trending")
async def get_trending(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Get trending diseases and specialty tags from last 7 days."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Top diseases by post count
    disease_result = await db.execute(
        select(DoctorPost.disease_name, func.count(DoctorPost.id).label("count"))
        .where(DoctorPost.created_at >= week_ago)
        .group_by(DoctorPost.disease_name)
        .order_by(desc("count"))
        .limit(10)
    )
    trending_diseases = [
        {"name": row[0], "post_count": row[1]}
        for row in disease_result.all()
    ]

    # Top specialty tags
    all_posts = await db.execute(
        select(DoctorPost.specialty_tags)
        .where(DoctorPost.created_at >= week_ago)
    )
    tag_counts: dict = {}
    for row in all_posts.all():
        for tag in (row[0] or []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    trending_tags = [
        {"tag": k, "count": v}
        for k, v in sorted(tag_counts.items(), key=lambda x: -x[1])[:15]
    ]

    # Recent post count
    total_recent = await db.scalar(
        select(func.count(DoctorPost.id)).where(DoctorPost.created_at >= week_ago)
    ) or 0

    return {
        "trending_diseases": trending_diseases,
        "trending_tags": trending_tags,
        "posts_this_week": total_recent,
    }


# ─── Stories ───────────────────────────────────────────────────────────────────

@router.get("/stories", response_model=List[DoctorPostResponse])
async def get_stories(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Get top 6 highest-engagement posts from the last 24 hours."""
    day_ago = datetime.now(timezone.utc) - timedelta(hours=24)

    # Get recent posts
    result = await db.execute(
        select(DoctorPost)
        .where(DoctorPost.created_at >= day_ago)
        .order_by(desc(DoctorPost.created_at))
        .limit(20)
    )
    posts = result.scalars().unique().all()

    # Enrich and sort by engagement
    enriched = []
    for post in posts:
        resp = await _enrich_post(post, db, doctor)
        enriched.append(resp)

    enriched.sort(key=lambda p: p.likes_count + p.comments_count * 2, reverse=True)
    return enriched[:6]


# ─── Hashtag Search ─────────────────────────────────────────────────────────────

@router.get("/hashtags")
async def get_hashtags(
    db: AsyncSession = Depends(get_db),
    _: Doctor = Depends(get_current_doctor_profile)
):
    """Get top hashtags (specialty tags) with post counts."""
    all_posts = await db.execute(select(DoctorPost.specialty_tags))
    tag_counts: dict = {}
    for row in all_posts.all():
        for tag in (row[0] or []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return sorted(
        [{"tag": k, "count": v} for k, v in tag_counts.items()],
        key=lambda x: -x["count"]
    )[:30]


# ─── Full-Text Search ──────────────────────────────────────────────────────────

@router.get("/search", response_model=List[DoctorPostResponse])
async def search_hub(
    q: str = Query(..., min_length=2, description="Search query"),
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Full-text search across post disease names, findings, and diagnoses."""
    stmt = (
        select(DoctorPost)
        .where(
            or_(
                DoctorPost.disease_name.ilike(f"%{q}%"),
                DoctorPost.clinical_findings.ilike(f"%{q}%"),
                DoctorPost.diagnosis.ilike(f"%{q}%"),
                DoctorPost.treatment_plan.ilike(f"%{q}%"),
            )
        )
        .order_by(desc(DoctorPost.created_at))
        .limit(20)
    )
    result = await db.execute(stmt)
    posts = result.scalars().unique().all()
    return [await _enrich_post(p, db, doctor) for p in posts]


# ─── Explore ───────────────────────────────────────────────────────────────────

@router.get("/explore")
async def explore_doctors(
    specialty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Explore verified doctors with their post and engagement stats."""
    stmt = select(Doctor).where(Doctor.verification_status == "verified")
    if specialty:
        stmt = stmt.where(Doctor.specialization.ilike(f"%{specialty}%"))
    stmt = stmt.limit(20)

    result = await db.execute(stmt)
    doctors = result.scalars().unique().all()

    profiles = []
    for doc in doctors:
        if doc.id == doctor.id:
            continue
        post_count = await db.scalar(
            select(func.count(DoctorPost.id)).where(DoctorPost.author_id == doc.id)
        ) or 0
        profiles.append({
            "id": str(doc.id),
            "full_name": getattr(doc, "full_name", "Dr. Physician"),
            "specialization": getattr(doc, "specialization", "General Practice"),
            "verification_status": doc.verification_status,
            "post_count": post_count,
        })

    profiles.sort(key=lambda x: -x["post_count"])
    return profiles


# ─── Create Post ───────────────────────────────────────────────────────────────

@router.post("/posts", response_model=DoctorPostResponse)
async def create_post(
    post_in: DoctorPostCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Create a structured clinical post."""
    if doctor.verification_status != "verified":
        raise HTTPException(status_code=403, detail="Only verified doctors can post.")

    post = DoctorPost(
        author_id=doctor.id,
        disease_name=post_in.disease_name,
        clinical_findings=post_in.clinical_findings,
        diagnosis=post_in.diagnosis,
        treatment_plan=post_in.treatment_plan,
        drugs_used=post_in.drugs_used,
        specialty_tags=post_in.specialty_tags
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    # Handle attachments
    if post_in.attachment_ids:
        stmt = select(FileObject).where(FileObject.id.in_(post_in.attachment_ids))
        file_objs = (await db.execute(stmt)).scalars().all()
        for f_obj in file_objs:
            attachment = PostAttachment(
                post_id=post.id,
                file_url=f"/api/v1/files/{f_obj.id}/download",
                file_type=f_obj.mime_type
            )
            db.add(attachment)
        await db.commit()
        await db.refresh(post)

    resp = DoctorPostResponse.model_validate(post)

    # Trigger AI ingestion in background
    background_tasks.add_task(_trigger_ingestion, post.id)

    # Broadcast to all connected clients
    await manager.broadcast("hub_new_post", resp.model_dump(mode='json'))

    return resp


# ─── Like ──────────────────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Toggle a like on a post and trigger credibility refresh."""
    post = await db.scalar(select(DoctorPost).where(DoctorPost.id == post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like = await db.scalar(select(PostLike).where(PostLike.post_id == post_id, PostLike.doctor_id == doctor.id))
    if like:
        await db.delete(like)
        liked = False
    else:
        new_like = PostLike(post_id=post_id, doctor_id=doctor.id)
        db.add(new_like)
        liked = True

    await db.commit()

    likes_count = await db.scalar(
        select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
    ) or 0

    # Refresh AI credibility weight when post gets liked
    if liked:
        background_tasks.add_task(_trigger_credibility_refresh, post_id)

    await manager.broadcast("hub_post_liked", {
        "post_id": str(post_id),
        "likes_count": likes_count
    })

    return {"liked": liked, "likes_count": likes_count}


# ─── Comment ───────────────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/comments", response_model=PostCommentResponse)
async def add_comment(
    post_id: uuid.UUID,
    comment_in: PostCommentCreate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Add a peer-review comment to a post."""
    post = await db.scalar(select(DoctorPost).where(DoctorPost.id == post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = PostComment(post_id=post_id, author_id=doctor.id, content=comment_in.content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    comments_count = await db.scalar(
        select(func.count(PostComment.id)).where(PostComment.post_id == post_id)
    ) or 0
    await manager.broadcast("hub_new_comment", {
        "post_id": str(post_id),
        "comments_count": comments_count
    })

    return comment


@router.get("/posts/{post_id}/comments", response_model=List[PostCommentResponse])
async def get_comments(
    post_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: Doctor = Depends(get_current_doctor_profile)
):
    """Get paginated comment thread for a post."""
    post = await db.scalar(select(DoctorPost).where(DoctorPost.id == post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.scalars(
        select(PostComment)
        .where(PostComment.post_id == post_id)
        .order_by(PostComment.created_at.asc())
        .offset(skip).limit(limit)
    )
    return [PostCommentResponse.model_validate(c) for c in result.all()]


# ─── Bookmark ──────────────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/bookmark")
async def toggle_bookmark(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Toggle a bookmark on a post."""
    post = await db.scalar(select(DoctorPost).where(DoctorPost.id == post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    bookmark = await db.scalar(
        select(PostBookmark).where(PostBookmark.post_id == post_id, PostBookmark.doctor_id == doctor.id)
    )
    if bookmark:
        await db.delete(bookmark)
        bookmarked = False
    else:
        new_bookmark = PostBookmark(post_id=post_id, doctor_id=doctor.id)
        db.add(new_bookmark)
        bookmarked = True

    await db.commit()
    return {"bookmarked": bookmarked}


# ─── Doctor Posts ───────────────────────────────────────────────────────────────

@router.get("/profiles/{doctor_id}/posts", response_model=List[DoctorPostResponse])
async def get_doctor_posts(
    doctor_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Get posts for a specific doctor profile."""
    stmt = (
        select(DoctorPost)
        .where(DoctorPost.author_id == doctor_id)
        .order_by(desc(DoctorPost.created_at))
        .offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    posts = result.scalars().unique().all()
    return [await _enrich_post(p, db, current_doctor) for p in posts]
