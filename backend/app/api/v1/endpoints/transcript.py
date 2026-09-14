"""DocAssistIQ — Transcript API Endpoints (Phase 27)."""

import uuid
import structlog

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.platform import API_RESPONSES
from app.authorization import require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.models.consultation import Consultation
from app.models.transcript import Transcript, TranscriptSegment
from app.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
    TranscriptSegmentResponse,
    TranscriptCorrection,
)

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/consultations", tags=["Transcripts"])


@router.get("/{consultation_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    consultation_id: uuid.UUID,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the transcript for a consultation."""
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    transcript = await db.scalar(  # type: ignore[assignment]

        select(Transcript)
        .options(selectinload(Transcript.segments))
        .where(Transcript.consultation_id == consultation_id)
    )
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    return transcript


@router.post("/{consultation_id}/transcript", response_model=TranscriptResponse)
async def save_transcript(
    consultation_id: uuid.UUID,
    payload: TranscriptCreate,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Save a new transcript (from streaming ASR)."""
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Delete existing if any (overwriting the whole transcript)
    existing = await db.scalar(
        select(Transcript).where(Transcript.consultation_id == consultation_id)
    )
    if existing:
        await db.delete(existing)
        
    transcript = Transcript(
        consultation_id=consultation_id,
        status=payload.status,
    )
    db.add(transcript)
    await db.flush()
    
    for seg in payload.segments:
        segment = TranscriptSegment(
            transcript_id=transcript.id,
            start_time=seg.start_time,
            end_time=seg.end_time,
            speaker_label=seg.speaker_label,
            speaker_confidence=seg.speaker_confidence,
            speaker_source=seg.speaker_source,
            raw_text=seg.raw_text,
            processed_text=seg.processed_text,
            clinician_corrected_text=seg.clinician_corrected_text,
            is_corrected=seg.is_corrected,
        )
        db.add(segment)
        
    await db.commit()
    
    # Reload with segments
    transcript = await db.scalar(  # type: ignore[assignment]

        select(Transcript)
        .options(selectinload(Transcript.segments))
        .where(Transcript.id == transcript.id)
    )
    return transcript


@router.patch("/{consultation_id}/transcript/segments/{segment_id}", response_model=TranscriptSegmentResponse)
async def correct_segment(
    consultation_id: uuid.UUID,
    segment_id: uuid.UUID,
    payload: TranscriptCorrection,
    doctor: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Clinician correction of a single transcript segment."""
    consultation = await db.scalar(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    segment = await db.scalar(
        select(TranscriptSegment)
        .join(Transcript)
        .where(
            TranscriptSegment.id == segment_id,
            Transcript.consultation_id == consultation_id
        )
    )
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
        
    segment.clinician_corrected_text = payload.clinician_corrected_text
    segment.is_corrected = True
    
    await db.commit()
    await db.refresh(segment)
    
    log.info("transcript_segment_corrected", segment_id=segment.id, doctor_id=doctor.id)
    return segment
