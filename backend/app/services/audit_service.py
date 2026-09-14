"""DocAssistIQ — Audit Service.

Provides a unified interface for recording clinical and system audit events.
Audit logs are used for compliance, forensic tracing, and security auditing.
"""

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_event(
    session: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    diff: str | None = None,
    severity: str = "info",
    request: Request | None = None,
) -> None:
    """Record a new audit event in the database.

    Args:
        session: An active database session (does not need to be committed by caller,
                 but the caller's transaction will persist this).
        action: Past-tense verb representing the action (e.g. 'consultation.created').
        entity_type: Broad category of the entity (e.g. 'consultation').
        entity_id: UUID of the specific entity affected.
        actor_id: UUID of the user who performed the action.
        tenant_id: Tenant context (if applicable, else pulled from session info).
        diff: Optional JSON-encoded string describing changes.
        severity: 'info', 'warning', or 'critical'.
        request: FastAPI Request object for extracting IP and User-Agent.
    """
    if not tenant_id:
        tenant_id = session.info.get("tenant_id")

    ip_address = None
    user_agent = None
    request_id = None

    if request:
        if request.client:
            ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        request_id = request.headers.get("x-request-id")

    log_entry = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        diff=diff,
        severity=severity,
    )
    
    session.add(log_entry)
    # Note: We rely on the caller's session commit to flush this.
    # If the caller rolls back, the audit log rolls back too, which is generally 
    # correct for transactional state changes (we don't want to audit a creation that failed).
