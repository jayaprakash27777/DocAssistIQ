"""DocAssistIQ — Doctor Profile and Verification Endpoints (Phase 10).

Endpoints:
  POST   /doctors/me           — create own doctor profile (doctor role)
  GET    /doctors/me           — get own doctor profile (doctor role)
  PATCH  /doctors/me           — update own doctor profile (doctor role)

  GET    /doctors/pending      — list pending reviews (admin only)
  POST   /doctors/{id}/verify  — approve or reject doctor (admin only)
  GET    /doctors/{id}         — get any doctor profile (admin only)

Doctor verification state machine:
  pending → verified  [admin: POST .../verify {action: 'verify'}]
  pending → rejected  [admin: POST .../verify {action: 'reject', rejection_reason: '...'}]
  verified → pending  [auto: doctor updates credential_reference / credential_body / specialty]
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse
from app.authorization import require_admin, require_doctor
from app.dependencies import get_db
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdate, VerifyDoctorRequest
from app.services import doctor_service

router = APIRouter(prefix="/doctors", tags=["Doctor Profiles"])

# ── Doctor self-service ───────────────────────────────────────


@router.post(
    "/me",
    response_model=DoctorResponse,
    status_code=201,
    summary="Create own doctor profile",
    description=(
        "Creates the authenticated user's doctor profile with status=pending. "
        "Only one profile per user is allowed."
    ),
    responses=API_RESPONSES,
)
async def create_my_profile(
    payload: DoctorCreate,
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> DoctorResponse:
    doctor = await doctor_service.create_doctor_profile(db, user.id, payload)
    return DoctorResponse.model_validate(doctor)


@router.get(
    "/me",
    response_model=DoctorResponse,
    summary="Get own doctor profile",
    responses=API_RESPONSES,
)
async def get_my_profile(
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> DoctorResponse:
    from app.exceptions import NotFoundError

    doctor = await doctor_service.get_doctor_by_user(db, user.id)
    if doctor is None:
        raise NotFoundError("No doctor profile found for this account", code="DOCTOR_NOT_FOUND")
    return DoctorResponse.model_validate(doctor)


@router.patch(
    "/me",
    response_model=DoctorResponse,
    summary="Update own doctor profile",
    description=(
        "Update profile fields. If any credential field changes while status "
        "is 'verified', the status reverts to 'pending' for re-verification."
    ),
    responses=API_RESPONSES,
)
async def update_my_profile(
    payload: DoctorUpdate,
    user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> DoctorResponse:
    doctor = await doctor_service.update_doctor_profile(db, user.id, payload)
    return DoctorResponse.model_validate(doctor)


# ── Admin verification ────────────────────────────────────────


@router.get(
    "/pending",
    response_model=PagedResponse[DoctorResponse],
    summary="List pending doctor verifications (admin only)",
    responses=API_RESPONSES,
)
async def list_pending(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PagedResponse[DoctorResponse]:
    doctors, total = await doctor_service.list_pending_doctors(db, page, page_size)
    pages = max(1, -(-total // page_size))  # ceil division
    return PagedResponse(
        items=[DoctorResponse.model_validate(d) for d in doctors],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get doctor profile by ID (admin only)",
    responses=API_RESPONSES,
)
async def get_doctor(
    doctor_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DoctorResponse:
    doctor = await doctor_service.get_doctor_by_id(db, doctor_id)
    return DoctorResponse.model_validate(doctor)


@router.post(
    "/{doctor_id}/verify",
    response_model=DoctorResponse,
    summary="Approve or reject doctor verification (admin only)",
    description=(
        "Admin reviews a pending doctor profile. "
        "action='verify' → status becomes 'verified'. "
        "action='reject' → status becomes 'rejected' (rejection_reason required). "
        "Only doctors currently in 'pending' status can be acted on."
    ),
    responses=API_RESPONSES,
)
async def verify_doctor(
    doctor_id: uuid.UUID,
    payload: VerifyDoctorRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DoctorResponse:
    doctor = await doctor_service.admin_verify_doctor(db, admin, doctor_id, payload)
    return DoctorResponse.model_validate(doctor)
