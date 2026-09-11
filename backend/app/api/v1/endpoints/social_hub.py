import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_doctor_profile
from app.models.doctor import Doctor
from app.models.file import FileObject
from app.models.social import DoctorPost, PostLike, PostComment, PostAttachment, PostBookmark
from app.schemas.social import (
    DoctorPostCreate, DoctorPostResponse,
    PostCommentCreate, PostCommentResponse
)
from app.api.v1.endpoints.ws import manager
from app.services.ingestion.social_ingester import ingest_doctor_post
from app.database import AsyncSessionLocal

router = APIRouter()

async def _trigger_ingestion(post_id: uuid.UUID):
    async with AsyncSessionLocal() as db:
        post = await db.scalar(select(DoctorPost).where(DoctorPost.id == post_id))
        if post:
            await ingest_doctor_post(db, post)

@router.get("/feed", response_model=List[DoctorPostResponse])
async def get_social_feed(
    skip: int = 0,
    limit: int = 20,
    disease: str = None,
    specialty: str = None,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Get the social timeline of verified doctor posts with filtering."""
    stmt = select(DoctorPost).order_by(DoctorPost.created_at.desc()).offset(skip).limit(limit)
    
    if disease:
        stmt = stmt.where(DoctorPost.disease_name.ilike(f"%{disease}%"))
    if specialty:
        stmt = stmt.where(DoctorPost.specialty_tags.contains([specialty]))
        
    result = await db.execute(stmt)
    posts = result.scalars().unique().all()
    
    response_posts = []
    for post in posts:
        # Load relationships (In production, use joinedload or subqueryload)
        likes_count = await db.scalar(select(func.count(PostLike.id)).where(PostLike.post_id == post.id))
        comments_count = await db.scalar(select(func.count(PostComment.id)).where(PostComment.post_id == post.id))
        is_liked = await db.scalar(select(PostLike).where(PostLike.post_id == post.id, PostLike.doctor_id == doctor.id))
        is_bookmarked = await db.scalar(select(PostBookmark).where(PostBookmark.post_id == post.id, PostBookmark.doctor_id == doctor.id))
        
        # Get top 3 comments
        comments = await db.scalars(select(PostComment).where(PostComment.post_id == post.id).order_by(PostComment.created_at.desc()).limit(3))
        
        resp = DoctorPostResponse.model_validate(post)
        resp.likes_count = likes_count or 0
        resp.comments_count = comments_count or 0
        resp.is_liked_by_me = bool(is_liked)
        resp.is_bookmarked_by_me = bool(is_bookmarked)
        resp.comments = list(comments)
        response_posts.append(resp)
        
    return response_posts

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
    
    # Handle attachments securely (using the FileObject uploaded via /files)
    if post_in.attachment_ids:
        stmt = select(FileObject).where(FileObject.id.in_(post_in.attachment_ids))
        file_objs = (await db.execute(stmt)).scalars().all()
        for f_obj in file_objs:
            attachment = PostAttachment(
                post_id=post.id,
                file_url=f"/api/v1/files/{f_obj.id}/download",
                file_type=f_obj.content_type
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

@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Toggle a like on a post."""
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
    
    # Broadcast the like update
    # We broadcast the total like count for the post so clients can just update the number
    likes_count = await db.scalar(select(func.count(PostLike.id)).where(PostLike.post_id == post_id))
    await manager.broadcast("hub_post_liked", {
        "post_id": str(post_id),
        "likes_count": likes_count or 0
    })
    
    return {"liked": liked}

@router.post("/posts/{post_id}/comments", response_model=PostCommentResponse)
async def add_comment(
    post_id: uuid.UUID,
    comment_in: PostCommentCreate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Add a comment to a post."""
    post = await db.scalar(select(DoctorPost).where(DoctorPost.id == post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    comment = PostComment(
        post_id=post_id,
        author_id=doctor.id,
        content=comment_in.content
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Broadcast comment update
    comments_count = await db.scalar(select(func.count(PostComment.id)).where(PostComment.post_id == post_id))
    await manager.broadcast("hub_new_comment", {
        "post_id": str(post_id),
        "comments_count": comments_count or 0
    })
    
    return comment

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
        
    bookmark = await db.scalar(select(PostBookmark).where(PostBookmark.post_id == post_id, PostBookmark.doctor_id == doctor.id))
    if bookmark:
        await db.delete(bookmark)
        bookmarked = False
    else:
        new_bookmark = PostBookmark(post_id=post_id, doctor_id=doctor.id)
        db.add(new_bookmark)
        bookmarked = True
        
    await db.commit()
    return {"bookmarked": bookmarked}

@router.get("/profiles/{doctor_id}/posts", response_model=List[DoctorPostResponse])
async def get_doctor_posts(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor_profile)
):
    """Get posts for a specific doctor profile."""
    stmt = select(DoctorPost).where(DoctorPost.author_id == doctor_id).order_by(DoctorPost.created_at.desc())
    result = await db.execute(stmt)
    posts = result.scalars().unique().all()
    
    # We omit like/comment counts here for brevity, but in a real system they would be included.
    return [DoctorPostResponse.model_validate(p) for p in posts]
