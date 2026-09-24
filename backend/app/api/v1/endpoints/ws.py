"""DocAssistIQ — WebSocket Streaming Endpoint (Phase 23).

Hardened Realtime Channel with sequence tracking, duplicate detection,
and ordered processing.
"""

from __future__ import annotations

import asyncio
import json
import uuid as _uuid
from datetime import datetime, timezone
from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ValidationError, Field

from app.config import Settings, get_settings
from app.dependencies import get_db, get_settings_dep
from app.models.user import User
from app.services.auth_service import decode_token
import base64
from app.services.asr_service import asr_service

log = structlog.get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


class WSEnvelope(BaseModel):
    type: str = Field(..., max_length=50)
    connection_id: str
    sequence_number: int
    timestamp: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    ack_seq: int | None = None


class ConnectionState:
    def __init__(self, websocket: WebSocket, user_id: str, connection_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id
        self.out_seq = 0
        self.in_seq = -1  # Last seen sequence number from client
        self.last_heartbeat = datetime.now(timezone.utc)
        self.closed = False
        self.audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.asr_task: asyncio.Task[None] | None = None

    async def send_msg(self, msg_type: str, payload: dict, ack: int | None = None):
        if self.closed:
            return
        self.out_seq += 1
        msg = WSEnvelope(
            type=msg_type,
            connection_id=self.connection_id,
            sequence_number=self.out_seq,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
            ack_seq=ack or self.in_seq if self.in_seq >= 0 else None
        )
        try:
            await self.websocket.send_text(msg.model_dump_json())
        except Exception as e:
            log.error("ws_send_failed", conn=self.connection_id, err=str(e))
            self.closed = True

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, ConnectionState] = {}

    def connect(self, state: ConnectionState):
        self.active_connections[state.connection_id] = state

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            self.active_connections[connection_id].closed = True
            del self.active_connections[connection_id]

    async def broadcast(self, msg_type: str, payload: dict):
        for conn in list(self.active_connections.values()):
            await conn.send_msg(msg_type, payload)


manager = ConnectionManager()
_HEARTBEAT_INTERVAL_S = 10
_STALE_TIMEOUT_S = 35


@router.websocket("/ws/v1/stream")
@router.websocket("/api/v1/ws/v1/stream")
async def ws_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> None:
    """Authenticated WebSocket stream with sequenced reliable delivery."""

    # 1. Auth Handshake
    try:
        payload = decode_token(token, settings)
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=4001)
            return
            
        user_uuid = _uuid.UUID(user_id_str)
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            await websocket.close(code=4003)
            return
            
    except Exception:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    connection_id = str(_uuid.uuid4())
    state = ConnectionState(websocket, user_id_str, connection_id)
    manager.connect(state)
    
    log.info("ws_connected", user_id=user_id_str, conn=connection_id)

    # Initial connect ack
    await state.send_msg("connected", {"user_id": user_id_str})

    # Background task for heartbeat & stale detection
    async def heartbeat_task():
        while not state.closed:
            await asyncio.sleep(_HEARTBEAT_INTERVAL_S)
            if state.closed:
                break
            
            # Check stale connection
            elapsed = (datetime.now(timezone.utc) - state.last_heartbeat).total_seconds()
            if elapsed > _STALE_TIMEOUT_S:
                log.warning("ws_stale_connection_closed", conn=connection_id)
                state.closed = True
                try:
                    await websocket.close(code=4008)
                except Exception:
                    pass
                break
                
            await state.send_msg("heartbeat", {})

    htask = asyncio.create_task(heartbeat_task())

    # Lazy ASR processor task (only started when client streams audio)
    def ensure_asr_task():
        if state.asr_task is None or state.asr_task.done():
            async def asr_processor():
                try:
                    async for msg in asr_service.process_stream(state.audio_queue):
                        if state.closed:
                            break
                        payload = {"text": msg.get("text", ""), "message": msg.get("message", "")}
                        if "diarization" in msg:
                            payload["diarization"] = msg["diarization"]
                        await state.send_msg(msg["type"], payload)
                except Exception as e:
                    log.error("asr_processor_error", err=str(e), conn=connection_id)
                    if not state.closed:
                        await state.send_msg("asr_error", {"message": "ASR processing failed"})
                        
            state.asr_task = asyncio.create_task(asr_processor())


    # Read loop
    try:
        while True:
            text = await websocket.receive_text()
            state.last_heartbeat = datetime.now(timezone.utc)
            
            try:
                data = json.loads(text)
                envelope = WSEnvelope(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                log.warning("ws_malformed_message", err=str(e), conn=connection_id)
                await state.send_msg("error", {"code": "MALFORMED_ENVELOPE", "details": str(e)})
                continue
                
            # Enforce Sequence Ordering and Duplicate Detection
            if envelope.sequence_number <= state.in_seq:
                log.debug("ws_duplicate_msg", seq=envelope.sequence_number, conn=connection_id)
                await state.send_msg("ack", {}, ack=envelope.sequence_number)
                continue
                
            state.in_seq = envelope.sequence_number
            
            # Handle standard types
            if envelope.type == "ping" or envelope.type == "heartbeat":
                await state.send_msg("pong", {}, ack=envelope.sequence_number)
                continue
                
            # Handle audio streaming
            if envelope.type == "audio_chunk":
                b64_data = envelope.payload.get("data")
                if b64_data:
                    try:
                        raw_bytes = base64.b64decode(b64_data)
                        await state.audio_queue.put(raw_bytes)
                    except Exception:
                        pass
                await state.send_msg("ack", {}, ack=envelope.sequence_number)
                continue
                
            if envelope.type == "audio_stop":
                await state.audio_queue.put(None)
                await state.send_msg("ack", {}, ack=envelope.sequence_number)
                continue

            # Real-time differential calculation over WebSocket (<20ms)
            if envelope.type in ("realtime_differential", "clinical_query"):
                symptoms = envelope.payload.get("symptoms", [])
                text_input = envelope.payload.get("text", "")
                try:
                    from app.services.clinical_reasoning_engine import clinical_reasoning_engine
                    import time
                    t0 = time.perf_counter()
                    if not symptoms and text_input:
                        from app.services.representation_service import _extract_from_text
                        ext = _extract_from_text(text_input)
                        symptoms = [s.get("name", "") for s in ext.get("symptoms", [])]
                    
                    predictions = clinical_reasoning_engine.score_all_diseases(
                        patient_symptoms=symptoms,
                        negated_symptoms=envelope.payload.get("negations", []),
                        countries_visited=envelope.payload.get("countries_visited", []),
                        days_since_return=envelope.payload.get("days_since_return"),
                        top_n=int(envelope.payload.get("top_n", 5))
                    )
                    latency = round((time.perf_counter() - t0) * 1000, 2)
                    pred_data = [
                        {
                            "disease": p.disease,
                            "score": p.score,
                            "supporting_findings": p.supporting_findings,
                            "missing_expected_findings": p.missing_expected_findings,
                            "explanation_hint": p.explanation_hint
                        } for p in predictions
                    ]
                    await state.send_msg("differential_update", {
                        "predictions": pred_data,
                        "latency_ms": latency,
                        "symptoms_evaluated": symptoms
                    }, ack=envelope.sequence_number)
                except Exception as e:
                    await state.send_msg("error", {"code": "DIFFERENTIAL_FAILED", "message": str(e)}, ack=envelope.sequence_number)
                continue

            # Real-time vitals / early warning assessment over WebSocket (<2ms)
            if envelope.type == "evaluate_vitals":
                vitals_list = envelope.payload.get("vitals", [])
                try:
                    from app.services.early_warning_service import early_warning_service
                    parsed = early_warning_service.parse_vitals(vitals_list)
                    news2 = early_warning_service.calculate_news2(parsed)
                    mews = early_warning_service.calculate_mews(parsed)
                    qsofa = early_warning_service.calculate_qsofa(parsed)
                    sirs = early_warning_service.calculate_sirs(parsed)
                    fb = early_warning_service.build_deterministic_clinical_fallback(
                        news2=news2, mews=mews, qsofa=qsofa, sirs=sirs, v=parsed, consultation_id=_uuid.uuid4()
                    )
                    await state.send_msg("early_warning_update", {
                        "news2": news2,
                        "mews": mews,
                        "qsofa": qsofa,
                        "sirs": sirs,
                        "is_high_risk": fb.is_high_risk,
                        "probability_percentage": fb.probability_percentage,
                        "primary_warning_flag": fb.primary_warning_flag,
                        "contributing_factors": fb.contributing_factors,
                        "recommended_immediate_actions": fb.recommended_immediate_actions
                    }, ack=envelope.sequence_number)
                except Exception as e:
                    await state.send_msg("error", {"code": "VITALS_EVAL_FAILED", "message": str(e)}, ack=envelope.sequence_number)
                continue

            # Real-time note drafting / ambient scribing stream over WebSocket
            if envelope.type in ("draft_note", "stream_note"):
                raw_text = envelope.payload.get("text", "")
                try:
                    from app.services.note_generator import note_generator_service, _extract_vitals_from_text, _extract_travel_history
                    vitals_extracted = _extract_vitals_from_text(raw_text)
                    travel_extracted = _extract_travel_history(raw_text)
                    
                    # Generate high-yield neuro-symbolic clinical draft
                    drafted = note_generator_service._fallback_draft([], raw_text, vitals_extracted, travel_extracted)
                    
                    # Stream non-empty sections incrementally
                    for sec_key, sec_val in drafted.items():
                        if sec_val:
                            await state.send_msg("note_section_chunk", {
                                "section": sec_key,
                                "text": sec_val,
                                "status": "draft"
                            })
                            await asyncio.sleep(0.005)

                    await state.send_msg("note_draft_complete", {
                        "body": drafted,
                        "vitals": vitals_extracted,
                        "travel": travel_extracted
                    }, ack=envelope.sequence_number)
                except Exception as e:
                    await state.send_msg("error", {"code": "NOTE_DRAFT_FAILED", "message": str(e)}, ack=envelope.sequence_number)
                continue
                
            # Acknowledge receipt
            await state.send_msg("ack", {}, ack=envelope.sequence_number)

    except WebSocketDisconnect:

        log.info("ws_disconnected", conn=connection_id)
    except Exception as exc:
        log.warning("ws_error", err=str(exc), conn=connection_id)
    finally:
        state.closed = True
        manager.disconnect(connection_id)
        htask.cancel()
        if state.asr_task:
            state.asr_task.cancel()
        await state.audio_queue.put(None)
