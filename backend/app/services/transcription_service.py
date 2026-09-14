"""DocAssistIQ — Streaming Transcription Service (Phase 24).

Provides an abstraction over Speech-to-Text (STT) providers.
Currently implements a Mock streaming provider for testing low-latency 
WebSocket pipelines without requiring API keys.
"""

import asyncio
import base64
import random
from typing import AsyncGenerator

import structlog

log = structlog.get_logger(__name__)

MOCK_PHRASES = [
    "Patient presents with a 3-day history of acute left-sided chest pain.",
    " The pain is described as sharp, non-radiating, and pleuritic.",
    " Vitals are stable: BP 120/80, HR 75, O2 sat 99% on room air.",
    " Physical exam reveals reproducible tenderness over the costochondral junctions.",
    " No murmurs, rubs, or gallops auscultated.",
    " Assessment is costochondritis.",
    " Will recommend NSAIDs and supportive care. Follow up if symptoms worsen."
]

class TranscriptionService:
    """Service to handle streaming audio transcription."""
    
    def __init__(self):
        self.phrase_index = 0

    async def stream_audio(self, audio_chunk_b64: str) -> AsyncGenerator[str, None]:
        """
        Takes a base64 encoded audio chunk, processes it, and yields transcript fragments.
        In a real provider (like Deepgram), this would push the chunk to an active websocket
        and yield results as they come back.
        """
        try:
            _ = base64.b64decode(audio_chunk_b64)
        except Exception as e:
            log.warning("Invalid base64 audio chunk received", error=str(e))
            return

        # Simulate network latency
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Yield a mock transcript chunk
        if random.random() > 0.4:  # 60% chance to yield text for this chunk
            phrase = MOCK_PHRASES[self.phrase_index % len(MOCK_PHRASES)]
            self.phrase_index += 1
            
            words = phrase.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.05)


# Singleton instance
transcription_service = TranscriptionService()
