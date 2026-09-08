"""DocAssistIQ — Doctor Service (Phase 10).

Implements the doctor profile management and verification state machine.

Verification state machine:
  pending  →  verified   [admin: action='verify']
  pending  →  rejected   [admin: action='reject' + required reason]
  rejected →  pending    [doctor: re-submits profile]
  verified →  pending    [doctor: updates credential fields]

RBAC:
  - Doctor manages own profile (role='doctor')
  - Admin reviews verification (role='admin')
  - Unverified doctors cannot access clinical endpoints (enforced per-endpoint)

Audit:
  Every verification state transition is logged to AuditLog.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import cast

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.audit import AuditLog
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorUpdate, VerifyDoctorRequest

log = structlog.get_logger(__name__)

# States that should revert to 'pending' when credentials are updated
_CREDENTIAL_FIELDS = {"specialty", "credential_reference", "credential_body"}


async def get_doctor_by_user(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Doctor | None:
    """Return the Doctor profile for the given user, or None."""
    result = await db.execute(
        select(Doctor).where(Doctor.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_doctor_by_id(
    db: AsyncSession,
    doctor_id: uuid.UUID,
) -> Doctor:
    """Return Doctor by PK, raise NotFoundError if absent."""
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id)
    )
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise NotFoundError("Doctor profile not found", code="DOCTOR_NOT_FOUND")
    return doctor


async def create_doctor_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: DoctorCreate,
) -> Doctor:
    """Create a doctor profile (pending status). One per user."""
    # Guard: one profile per user
    existing = await get_doctor_by_user(db, user_id)
    if existing is not None:
        raise ValidationError("A doctor profile already exists for this user", code="DOCTOR_PROFILE_EXISTS")

    doctor = Doctor(
        user_id=user_id,
        specialty=payload.specialty,
        credential_reference=payload.credential_reference,
        credential_body=payload.credential_body,
        bio=payload.bio,
        verification_status="pending",
    )

    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    _audit(db, actor_id=user_id, action="doctor.profile_created", entity=doctor)

    log.info("doctor_profile_created", user_id=str(user_id), doctor_id=str(doctor.id))
    return doctor


async def update_doctor_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: DoctorUpdate,
) -> Doctor:
    """
    Doctor updates their own profile.

    If any credential field changes AND the current status is 'verified',
    it is reset to 'pending' to require re-verification.
    """
    doctor = await get_doctor_by_user(db, user_id)
    if doctor is None:
        raise NotFoundError("Doctor profile not found", code="DOCTOR_NOT_FOUND")

    changes = payload.model_dump(exclude_unset=True)
    credential_changed = bool(_CREDENTIAL_FIELDS & set(changes.keys()))

    for field, value in changes.items():
        setattr(doctor, field, value)

    if credential_changed and doctor.verification_status == "verified":
        doctor.verification_status = "pending"
        doctor.verified_by_id = None
        doctor.rejection_reason = None
        log.info(
            "doctor_reverified_to_pending",
            doctor_id=str(doctor.id),
            reason="credential_fields_changed",
        )

    _audit(db, actor_id=user_id, action="doctor.profile_updated", entity=doctor)
    await db.commit()
    await db.refresh(doctor)

    return doctor


async def admin_verify_doctor(
    db: AsyncSession,
    admin_user: User,
    doctor_id: uuid.UUID,
    payload: VerifyDoctorRequest,
) -> Doctor:
    """
    Admin reviews a doctor's verification request.

    Actions:
      'verify' : pending → verified
      'reject' : pending → rejected (reason required)

    Raises:
      NotFoundError if doctor not found.
      ValidationError if doctor is not in 'pending' state.
    """
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id)
    )
    doctor = result.scalar_one_or_none()

    if doctor is None:
        raise NotFoundError("Doctor profile not found", code="DOCTOR_NOT_FOUND")

    if doctor.verification_status != "pending":
        raise ValidationError(
            f"Cannot act on a doctor whose status is '{doctor.verification_status}'. "
            "Only pending doctors can be reviewed.", code="DOCTOR_NOT_PENDING"
        )

    if payload.action == "verify":
        doctor.verification_status = "verified"
        doctor.verified_by_id = admin_user.id
        doctor.rejection_reason = None
        action = "doctor.verified"
    else:
        doctor.verification_status = "rejected"
        doctor.verified_by_id = admin_user.id
        doctor.rejection_reason = payload.rejection_reason
        action = "doctor.rejected"

    _audit(db, actor_id=admin_user.id, action=action, entity=doctor)
    await db.commit()
    await db.refresh(doctor)

    log.info(
        action,
        admin_id=str(admin_user.id),
        doctor_id=str(doctor_id),
        status=doctor.verification_status,
    )
    return doctor


async def list_pending_doctors(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Doctor], int]:
    """Return all doctors with verification_status='pending' (admin only)."""
    offset = (page - 1) * page_size

    async with db.begin():
        # Total count
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count()).select_from(Doctor).where(
                Doctor.verification_status == "pending"
            )
        )
        total = count_result.scalar_one()

        # Page
        result = await db.execute(
            select(Doctor)
            .where(Doctor.verification_status == "pending")
            .order_by(Doctor.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        doctors = list(result.scalars().all())

    return doctors, total


# ── Internal helpers ──────────────────────────────────────────


def _audit(
    db: AsyncSession,
    actor_id: uuid.UUID,
    action: str,
    entity: Doctor,
) -> None:
    """Append an audit log entry (not flushed here; call inside an open transaction)."""
    log_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type="doctor",
        entity_id=entity.id,
        severity="info",
    )
    db.add(log_entry)
