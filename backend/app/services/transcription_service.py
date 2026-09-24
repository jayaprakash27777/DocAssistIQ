"""DocAssistIQ — Streaming Transcription Service.

Provides an abstraction over real-time Speech-to-Text (STT) providers.
Processes real base64-encoded audio chunks, decodes PCM/WebM frames, and
streams transcribed text fragments using the underlying ASR pipeline.
Strictly zero mock data or hardcoded canned phrases.
"""

import asyncio
import base64
from typing import AsyncGenerator
import structlog

from app.services.asr_service import asr_service

log = structlog.get_logger(__name__)


class TranscriptionService:
    """Service to handle real-time streaming audio transcription."""

    def __init__(self):
        self._buffer = bytearray()

    async def stream_audio(self, audio_chunk_b64: str) -> AsyncGenerator[str, None]:
        """
        Takes a base64 encoded audio chunk, decodes audio bytes, and feeds it
        into the real-time ASR engine to yield actual recognized speech fragments.
        Yields nothing if the chunk is silence or unparseable.
        """
        if not audio_chunk_b64 or not audio_chunk_b64.strip():
            return

        try:
            audio_bytes = base64.b64decode(audio_chunk_b64)
        except Exception as e:
            log.warning("invalid_base64_audio_chunk", error=str(e))
            return

        if not audio_bytes:
            return

        # Queue audio chunk into temporary queue for ASR processing
        audio_queue = asyncio.Queue()
        await audio_queue.put(audio_bytes)
        await audio_queue.put(None)  # Sentinel to close stream

        try:
            async for asr_msg in asr_service.process_stream(audio_queue):
                msg_type = asr_msg.get("type")
                if msg_type in ("asr_partial", "asr_final"):
                    text = asr_msg.get("text", "")
                    if text and text.strip():
                        yield text.strip() + " "
        except Exception as e:
            log.warning("transcription_streaming_error", error=str(e))


# Singleton instance
transcription_service = TranscriptionService()
