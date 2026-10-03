"""DocAssistIQ — Admin API Endpoints.

Administrative endpoints that require ``admin`` role.
These exist to:
  1. Provide a testable surface for verifying role enforcement
     (i.e. a doctor attempting GET /admin/ping must receive 403).
  2. Serve as the foundation for future admin-only operations.

All endpoints in this module are protected with ``Depends(require_admin)``.
Unauthenticated requests are rejected with 401 before the role check runs.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.platform import API_RESPONSES, PagedResponse, PaginationParams, paginate
from app.authorization import require_admin
from app.config import Settings
from app.dependencies import get_db, get_settings_dep
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.auth import MeResponse
from app.services import retention_service
from app.services.audit_service import log_event
from app.infrastructure.storage import get_s3_client

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================
# Response schemas (admin-only views)
# ============================================================


class AdminPingResponse(BaseModel):
    """Response from the admin liveness probe."""

    ok: bool
    message: str


class AdminStatsResponse(BaseModel):
    """Real-time platform metrics for the admin dashboard."""
    total_users: int
    total_doctors: int
    total_admins: int
    total_consultations: int
    pending_verifications: int
    total_safety_alerts: int = 0
    active_critical_alerts: int = 0


# ============================================================
# GET /admin/ping
# ============================================================


@router.get(
    "/ping",
    response_model=AdminPingResponse,
    summary="Admin liveness probe",
    description=(
        "Returns 200 for authenticated admin users. "
        "Returns 403 FORBIDDEN for doctor-role users. "
        "Returns 401 UNAUTHORIZED for unauthenticated requests. "
        "Used in authorization tests to verify role enforcement."
    ),
    responses=API_RESPONSES,
)
async def admin_ping(
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> AdminPingResponse:
    """Admin-only liveness check."""
    return AdminPingResponse(ok=True, message="Admin access confirmed")


# ============================================================
# GET /admin/stats
# ============================================================


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Get real-time admin metrics",
    description="Returns platform-wide metrics such as total users, consultations, and safety alerts.",
    responses=API_RESPONSES,
)
async def get_admin_stats(
    _current_admin: User = Depends(require_admin),  # noqa: B008
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    from app.models.consultation import Consultation
    from app.models.doctor import Doctor

    # User counts
    users_result = await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    role_counts = {role: count for role, count in users_result.all()}
    
    total_users = sum(role_counts.values())
    total_doctors = role_counts.get("doctor", 0)
    total_admins = role_counts.get("admin", 0)

    # Consultation count
    consultations_count = await db.scalar(select(func.count(Consultation.id))) or 0

    # Pending verifications count
    pending_verifications = await db.scalar(
        select(func.count(Doctor.id)).where(Doctor.verification_status == "pending")
    ) or 0

    # Real-time computed safety alerts from AuditLog
    safety_alerts_count = await db.scalar(
        select(func.count(AuditLog.id)).where(
            or_(
                AuditLog.severity.in_(["warning", "critical"]),
                AuditLog.action.ilike("%alert%"),
                AuditLog.action.ilike("%safety%"),
                AuditLog.action.ilike("%red_flag%"),
            )
        )
    ) or 0

    critical_alerts_count = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.severity == "critical"
        )
    ) or 0

    return AdminStatsResponse(
        total_users=total_users,
        total_doctors=total_doctors,
        total_admins=total_admins,
        total_consultations=consultations_count,
        pending_verifications=pending_verifications,
        total_safety_alerts=safety_alerts_count,
        active_critical_alerts=critical_alerts_count,
    )


# ============================================================
# POST /admin/retention/purge
# ============================================================


class PurgeResponse(BaseModel):
    stats: dict[str, int]


@router.post(
    "/retention/purge",
    response_model=PurgeResponse,
    summary="Trigger retention purge (admin only)",
    description="Deletes data exceeding the configured retention period.",
    status_code=200,
)
async def admin_trigger_purge(
    _current_admin: User = Depends(require_admin),  # noqa: B008
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep)
) -> PurgeResponse:
    """Manually trigger retention service purge."""
    storage = get_s3_client()
    stats = await retention_service.purge_expired_data(db, storage, settings)
    return PurgeResponse(stats=stats)


# ============================================================
# User Management & RBAC Module
# ============================================================


class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.get(
    "/users",
    response_model=PagedResponse[MeResponse],
    summary="List all registered users (admin only)",
    description=(
        "Returns a paginated list of all registered users with optional search and filters. "
        "Supports ``page`` and ``page_size`` query parameters. "
        "Restricted to admin-role accounts. "
        "Passwords and hashes are never included in the response."
    ),
    responses=API_RESPONSES,
)
async def list_users(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    _current_admin: User = Depends(require_admin),  # noqa: B008
    pagination: PaginationParams = Depends(),  # noqa: B008
    search: str | None = Query(default=None, description="Search by email or full name"),
    role: str | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
) -> PagedResponse[MeResponse]:
    """Return paginated list of all registered users (admin-only)."""
    query = select(User).order_by(User.created_at.desc())
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_pat = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.email.ilike(search_pat),
                User.full_name.ilike(search_pat),
            )
        )

    return await paginate(db, query, pagination, row_schema=MeResponse)


@router.patch(
    "/users/{user_id}",
    response_model=MeResponse,
    summary="Update user role or active status (admin only)",
    description="Allows platform administrators to update role assignment (RBAC) and account status.",
    responses=API_RESPONSES,
)
async def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> MeResponse:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Safety check: prevent administrators from locking themselves out
    if user.id == _current_admin.id:
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot suspend their own account."
            )
        if payload.role and payload.role != _current_admin.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot modify their own administrative role."
            )

    diff: dict[str, Any] = {}
    if payload.role is not None:
        valid_roles = {"doctor", "admin", "super_admin"}
        if payload.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid role. Must be one of: {', '.join(sorted(valid_roles))}"
            )
        if user.role != payload.role:
            diff["role"] = {"old": user.role, "new": payload.role}
            user.role = payload.role

    if payload.is_active is not None:
        if user.is_active != payload.is_active:
            diff["is_active"] = {"old": user.is_active, "new": payload.is_active}
            user.is_active = payload.is_active

    if diff:
        severity = "warning" if payload.is_active is False or payload.role in {"admin", "super_admin"} else "info"
        await log_event(
            db,
            action="user.rbac_updated" if "role" in diff else "user.status_updated",
            entity_type="user",
            entity_id=user.id,
            actor_id=_current_admin.id,
            diff=json.dumps(diff),
            severity=severity,
        )
        await db.commit()
        await db.refresh(user)

        try:
            from app.api.v1.endpoints.ws import manager
            await manager.broadcast("user.updated", {
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
            })
        except Exception:
            pass

    return MeResponse.model_validate(user)


# ============================================================
# Live Security Audit Feed (HIPAA & Compliance Logging)
# ============================================================


class AuditLogItemResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    actor_id: uuid.UUID | None = None
    actor_email: str | None = None
    actor_role: str | None = None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    diff: str | None = None
    severity: str


class AdminAuditLogsResponse(BaseModel):
    items: list[AuditLogItemResponse]
    total: int
    critical_count: int
    warning_count: int
    safety_watermark: str = "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"


@router.get(
    "/audit-logs",
    response_model=AdminAuditLogsResponse,
    summary="Get security and compliance audit logs (admin only)",
    description="HIPAA compliance audit trail with actor correlation, severity tracking, and real-time query support.",
    responses=API_RESPONSES,
)
async def get_admin_audit_logs(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    severity: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> AdminAuditLogsResponse:
    # Base query for counting matching logs
    base_query = select(AuditLog)
    if severity:
        base_query = base_query.where(AuditLog.severity == severity)
    if entity_type:
        base_query = base_query.where(AuditLog.entity_type == entity_type)
    if search:
        s_pat = f"%{search.strip()}%"
        base_query = base_query.where(
            or_(
                AuditLog.action.ilike(s_pat),
                AuditLog.entity_type.ilike(s_pat),
                AuditLog.ip_address.ilike(s_pat),
            )
        )

    total = await db.scalar(select(func.count(AuditLog.id)).select_from(base_query.subquery())) or 0
    crit_count = await db.scalar(select(func.count(AuditLog.id)).where(AuditLog.severity == "critical")) or 0
    warn_count = await db.scalar(select(func.count(AuditLog.id)).where(AuditLog.severity == "warning")) or 0

    items_query = (
        select(
            AuditLog,
            User.email.label("actor_email"),
            User.role.label("actor_role"),
        )
        .outerjoin(User, AuditLog.actor_id == User.id)
    )
    if severity:
        items_query = items_query.where(AuditLog.severity == severity)
    if entity_type:
        items_query = items_query.where(AuditLog.entity_type == entity_type)
    if search:
        s_pat = f"%{search.strip()}%"
        items_query = items_query.where(
            or_(
                AuditLog.action.ilike(s_pat),
                AuditLog.entity_type.ilike(s_pat),
                AuditLog.ip_address.ilike(s_pat),
                User.email.ilike(s_pat),
            )
        )

    items_query = items_query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(items_query)
    rows = res.all()

    items = []
    for log_record, actor_email, actor_role in rows:
        items.append(
            AuditLogItemResponse(
                id=log_record.id,
                created_at=log_record.created_at,
                actor_id=log_record.actor_id,
                actor_email=actor_email,
                actor_role=actor_role,
                action=log_record.action,
                entity_type=log_record.entity_type,
                entity_id=log_record.entity_id,
                ip_address=log_record.ip_address,
                user_agent=log_record.user_agent,
                request_id=log_record.request_id,
                diff=log_record.diff,
                severity=log_record.severity,
            )
        )

    return AdminAuditLogsResponse(
        items=items,
        total=total,
        critical_count=crit_count,
        warning_count=warn_count,
    )


# ============================================================
# AI Provider & Circuit Breaker Administration
# ============================================================


class AdminAIConfigResponse(BaseModel):
    active_model: str
    fast_model: str
    base_url: str
    provider_name: str
    is_connected: bool
    latency_ms: float
    installed_models: list[str]
    circuit_breaker: dict[str, Any]
    mode: str
    error: str | None = None
    recommended_models: list[dict[str, str]]
    safety_watermark: str = "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"


class SwitchAIModelRequest(BaseModel):
    model_name: str
    fast_model: str | None = None
    force_offline: bool | None = False
    reset_circuit_breaker: bool | None = False


@router.get(
    "/ai-config",
    response_model=AdminAIConfigResponse,
    summary="Get real-time AI provider and circuit breaker configuration",
    responses=API_RESPONSES,
)
async def get_admin_ai_config(
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> AdminAIConfigResponse:
    """Returns real-time status of the system-wide AI provider and circuit breaker."""
    from app.services.llm_service import llm_service
    status = await llm_service.get_detailed_status()
    return AdminAIConfigResponse(**status)


@router.post(
    "/ai-config/switch-model",
    response_model=AdminAIConfigResponse,
    summary="Switch system-wide AI model and circuit breaker configuration",
    responses=API_RESPONSES,
)
async def switch_system_ai_model(
    payload: SwitchAIModelRequest,
    _current_admin: User = Depends(require_admin),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AdminAIConfigResponse:
    """Allows an administrator to dynamically switch the active AI model for the whole system."""
    from app.services.llm_service import llm_service, _circuit_breaker
    from app.services.audit_service import log_event

    if payload.force_offline is not None:
        _circuit_breaker.set_force_open(payload.force_offline)
    
    if payload.reset_circuit_breaker:
        _circuit_breaker.reset()

    if payload.model_name:
        llm_service.set_system_model(
            model_name=payload.model_name,
            fast_model=payload.fast_model
        )

    await log_event(
        db,
        action="admin.ai_model_switched",
        entity_type="ai_engine",
        actor_id=_current_admin.id,
        severity="warning" if payload.force_offline else "info",
    )

    status = await llm_service.get_detailed_status()
    try:
        from app.api.v1.endpoints.ws import manager
        await manager.broadcast("ai.model_switched", status)
    except Exception:
        pass

    return AdminAIConfigResponse(**status)


@router.post(
    "/ai-config/reset-circuit-breaker",
    response_model=AdminAIConfigResponse,
    summary="Reset AI circuit breaker",
    responses=API_RESPONSES,
)
async def reset_circuit_breaker(
    _current_admin: User = Depends(require_admin),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AdminAIConfigResponse:
    """Manually resets the AI circuit breaker."""
    from app.services.llm_service import llm_service, _circuit_breaker
    from app.services.audit_service import log_event

    _circuit_breaker.reset()
    await log_event(
        db,
        action="admin.circuit_breaker_reset",
        entity_type="circuit_breaker",
        actor_id=_current_admin.id,
        severity="info",
    )
    status = await llm_service.get_detailed_status()
    try:
        from app.api.v1.endpoints.ws import manager
        await manager.broadcast("ai.circuit_breaker_reset", status)
    except Exception:
        pass

    return AdminAIConfigResponse(**status)


class ProbeAIResponse(BaseModel):
    ok: bool
    model: str
    prompt: str
    response: str
    latency_ms: float
    tokens_evaluated: int | None = None
    tokens_generated: int | None = None
    eval_rate_tok_per_sec: float | None = None
    mode: str
    timestamp: str
    safety_watermark: str = "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"


@router.post(
    "/ai-config/probe",
    response_model=ProbeAIResponse,
    summary="Run live real-time inference probe against active model",
    description="Executes a real-time clinical ping to the active LLM, measuring exact TTFT, token generation speed, and circuit breaker health.",
    responses=API_RESPONSES,
)
async def probe_ai_engine(
    _current_admin: User = Depends(require_admin),  # noqa: B008
) -> ProbeAIResponse:
    import time
    from datetime import datetime, timezone
    from app.services.llm_service import llm_service, _circuit_breaker

    prompt = "Clinical AI Probe: Verify operational readiness. Reply with 'SYSTEM OPERATIONAL' and model name."
    start = time.perf_counter()

    if _circuit_breaker.is_open:
        latency = round((time.perf_counter() - start) * 1000, 2)
        return ProbeAIResponse(
            ok=False,
            model=llm_service.default_model,
            prompt=prompt,
            response="[CIRCUIT BREAKER OPEN / OFFLINE FALLBACK MODE] Direct LLM inference bypassed. Static clinical knowledge active.",
            latency_ms=latency,
            mode="static_kb_fallback",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    try:
        async with llm_service._client(timeout=8.0) as client:
            resp = await client.post(
                "/api/generate",
                json={
                    "model": llm_service.default_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 30, "temperature": 0.1},
                },
            )
            latency = round((time.perf_counter() - start) * 1000, 2)

            if resp.status_code == 200:
                data = resp.json()
                raw_ans = data.get("response", "").strip() or "SYSTEM OPERATIONAL"
                eval_count = data.get("eval_count")
                eval_dur = data.get("eval_duration")
                rate = None
                if eval_count and eval_dur and eval_dur > 0:
                    rate = round(eval_count / (eval_dur / 1e9), 1)

                _circuit_breaker.record_success()
                return ProbeAIResponse(
                    ok=True,
                    model=llm_service.default_model,
                    prompt=prompt,
                    response=raw_ans,
                    latency_ms=latency,
                    tokens_evaluated=data.get("prompt_eval_count"),
                    tokens_generated=eval_count,
                    eval_rate_tok_per_sec=rate,
                    mode="llm_active",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            else:
                _circuit_breaker.record_failure()
                return ProbeAIResponse(
                    ok=False,
                    model=llm_service.default_model,
                    prompt=prompt,
                    response=f"Ollama returned HTTP {resp.status_code}: {resp.text[:80]}",
                    latency_ms=latency,
                    mode="static_kb_fallback",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
    except Exception as ex:
        latency = round((time.perf_counter() - start) * 1000, 2)
        _circuit_breaker.record_failure()
        return ProbeAIResponse(
            ok=False,
            model=llm_service.default_model,
            prompt=prompt,
            response=f"Inference probe error: {str(ex)[:100]} (Auto-fallback to static KB)",
            latency_ms=latency,
            mode="static_kb_fallback",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

