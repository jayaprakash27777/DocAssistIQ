"""DocAssistIQ — WebSocket Streaming Endpoint.

Provides an authenticated real-time connection for the browser shell.
The client displays connection state: LIVE / CONNECTING / RECONNECTING / UNAVAILABLE.

Authentication:
  WebSocket connections cannot carry an Authorization header from browsers.
  JWT is passed as a ``token`` query parameter instead:
    ws://host/ws/v1/stream?token=<jwt>

Message types (server → client):
  {"type": "connected", "user_id": "...", "ts": "<iso>"}
  {"type": "ping", "ts": "<iso>"}

Close codes:
  4001 — invalid or expired token
  4003 — account inactive

Note: This is a Phase 8 skeleton. In later phases this connection will
carry real-time AI analysis results and clinical update events.
"""

from __future__ import annotations

import asyncio
import json
import uuid as _uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.dependencies import get_db, get_settings_dep
from app.models.user import User
from app.services.auth_service import decode_token

log = structlog.get_logger(__name__)

router = APIRouter(tags=["WebSocket"])

_PING_INTERVAL_S = 15


@router.websocket("/ws/v1/stream")
async def ws_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
    db: AsyncSession = Depends(get_db),  # noqa: B008 — FastAPI supports Depends in WS routes
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
) -> None:
    """Authenticated WebSocket stream for real-time shell state."""

    # ── Authenticate before accepting ─────────────────────────────────────
    try:
        payload = decode_token(token, settings)
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    # ── Load user from DB via injected session ─────────────────────────────
    try:
        user_uuid = _uuid.UUID(user_id_str)
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
    except Exception:
        await websocket.close(code=4001)
        return

    if user is None or not user.is_active:
        await websocket.close(code=4003)
        return

    # ── Accept connection ─────────────────────────────────────────────────
    await websocket.accept()
    log.info("ws_connected", user_id=user_id_str)

    ts = datetime.now(timezone.utc).isoformat()
    await websocket.send_text(
        json.dumps({"type": "connected", "user_id": user_id_str, "ts": ts})
    )

    # ── Ping loop ─────────────────────────────────────────────────────────
    try:
        while True:
            await asyncio.sleep(_PING_INTERVAL_S)
            ts = datetime.now(timezone.utc).isoformat()
            await websocket.send_text(json.dumps({"type": "ping", "ts": ts}))
    except WebSocketDisconnect:
        log.info("ws_disconnected", user_id=user_id_str)
    except Exception as exc:
        log.warning("ws_error", user_id=user_id_str, error=str(exc))
