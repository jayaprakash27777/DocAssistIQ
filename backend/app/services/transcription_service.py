"""DocAssistIQ — Streaming Transcription Service.

Provides an abstraction over real-time Speech-to-Text (STT) providers.
Processes real base64-encoded audio chunks, decodes PCM/WebM frames, and
streams transcribed text fragments using the underlying ASR pipeline.
Strictly zero mock data or hardcoded canned phrases.
"""

import asyncio
import base64
from typing import AsyncGenerator, Dict, Any, Optional
import structlog

from app.services.asr_service import asr_service

log = structlog.get_logger(__name__)


class TranscriptionService:
    """Service to handle real-time streaming audio transcription."""

    def __init__(self):
        self._buffer = bytearray()
        self._last_text = ""

    async def transcribe(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Transcribe a complete audio recording."""
        return await asr_service.transcribe_audio_bytes(audio_bytes)

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

        self._buffer.extend(audio_bytes)

        # Transcribe accumulated buffer
        try:
            result = await asr_service.transcribe_audio_bytes(bytes(self._buffer))
            text = (result.get("text") or "").strip()
            if text and text != self._last_text:
                new_fragment = text[len(self._last_text):].strip() if text.startswith(self._last_text) else text
                self._last_text = text
                if new_fragment:
                    yield new_fragment + " "
        except Exception as e:
            log.warning("transcription_streaming_error", error=str(e))

    def reset(self):
        """Reset internal streaming buffer."""
        self._buffer.clear()
        self._last_text = ""


# Singleton instance
transcription_service = TranscriptionService()

