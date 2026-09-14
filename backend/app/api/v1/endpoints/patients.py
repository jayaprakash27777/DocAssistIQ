import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.platform import API_RESPONSES
from app.authorization import require_permission
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.patient_profile import PatientProfile
from app.models.doctor import Doctor
from app.schemas.patient import (
    PatientProfileCreate,
    PatientProfileUpdate,
    PatientProfileResponse,
)

router = APIRouter(prefix="/patients", tags=["Patients"])

async def get_current_doctor_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    """Helper to get the doctor profile for the current user."""
    result = await db.execute(
        select(Doctor).where(Doctor.user_id == user.id)
    )
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for this user",
        )
    return doctor

@router.post("/", response_model=PatientProfileResponse, responses=API_RESPONSES)
async def create_patient_profile(
    profile_in: PatientProfileCreate,
    user: User = Depends(require_permission("patient", "create")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Create a new de-identified patient profile."""
    # Check if patient_ref already exists for this tenant
    stmt = select(PatientProfile).where(
        PatientProfile.tenant_id == doctor.tenant_id,
        PatientProfile.patient_ref == profile_in.patient_ref
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient reference already exists in this tenant"
        )
    
    new_profile = PatientProfile(
        tenant_id=doctor.tenant_id,
        patient_ref=profile_in.patient_ref,
        age_group=profile_in.age_group,
        biological_sex=profile_in.biological_sex,
        baseline_conditions=profile_in.baseline_conditions,
    )
    
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

@router.get("/", response_model=list[PatientProfileResponse], responses=API_RESPONSES)
async def list_patient_profiles(
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """List all patient profiles for the current tenant."""
    stmt = (
        select(PatientProfile)
        .where(PatientProfile.tenant_id == doctor.tenant_id)
        .options(selectinload(PatientProfile.sessions))
        .order_by(PatientProfile.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{profile_id}", response_model=PatientProfileResponse, responses=API_RESPONSES)
async def get_patient_profile(
    profile_id: uuid.UUID,
    user: User = Depends(require_permission("patient", "read")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific patient profile by ID, including their sessions."""
    stmt = (
        select(PatientProfile)
        .where(
            PatientProfile.id == profile_id,
            PatientProfile.tenant_id == doctor.tenant_id
        )
        .options(selectinload(PatientProfile.sessions))
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
        
    return profile

@router.get("/{profile_id}/timeline", responses=API_RESPONSES)
async def get_patient_timeline(
    profile_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
    event_type: str | None = Query(None, description="Filter by event_type"),
    user: User = Depends(require_permission("patient", "read")),
    doctor: Doctor = Depends(get_current_doctor_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get chronological timeline of events for a patient."""
    from app.services.timeline_service import get_patient_timeline as fetch_timeline
    
    # Check access to this patient profile
    stmt = select(PatientProfile).where(
        PatientProfile.id == profile_id,
        PatientProfile.tenant_id == doctor.tenant_id
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    filters = event_type.split(",") if event_type else None
    
    events = await fetch_timeline(db, profile_id, page_size, (page - 1) * page_size, filters or [])
    return {"events": events}

