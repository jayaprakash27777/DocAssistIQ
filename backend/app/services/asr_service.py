"""DocAssistIQ — Streaming ASR Service (Phase 25).

Integrates `faster-whisper` for real-time speech-to-text.
Decodes incoming WebM/Opus or MP4 chunks using `av`.
Provides an async generator yielding partial and final transcription segments.
"""

import asyncio
import io
import structlog
from typing import AsyncGenerator
import numpy as np
import time

from app.services.diarization_service import default_diarization_provider

try:
    import av  # type: ignore[import-untyped]
    from faster_whisper import WhisperModel  # type: ignore[import-untyped]
except ImportError:
    av = None  # type: ignore[assignment]
    WhisperModel = None  # type: ignore[assignment]

log = structlog.get_logger(__name__)

class ASRService:
    def __init__(self, model_size="base.en", device="cuda", compute_type="float16"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._load_lock = asyncio.Lock()
        self.sample_rate = 16000

    async def _ensure_model(self):
        if self.model is None and WhisperModel is not None:
            async with self._load_lock:
                if self.model is None:
                    log.info("asr_loading_model", size=self.model_size)
                    # We run blocking load in an executor to avoid stalling the event loop
                    try:
                        self.model = await asyncio.to_thread(
                            WhisperModel,
                            self.model_size,
                            device=self.device,
                            compute_type=self.compute_type,
                            download_root="./model_cache"
                        )
                        log.info("asr_model_loaded_gpu")
                    except Exception as e:
                        log.warning(f"Failed to load whisper on GPU: {e}. Falling back to CPU int8.")
                        self.model = await asyncio.to_thread(
                            WhisperModel,
                            self.model_size,
                            device="cpu",
                            compute_type="int8",
                            download_root="./model_cache"
                        )
                        log.info("asr_model_loaded_cpu")

    def _decode_audio_chunk(self, audio_data: bytes) -> np.ndarray:
        """Decode WebM/Opus or MP4 to 16kHz mono float32 numpy array."""
        if not av:
            return np.zeros(0, dtype=np.float32)
            
        try:
            container = av.open(io.BytesIO(audio_data), mode='r')
            resampler = av.AudioResampler(
                format='flt',
                layout='mono',
                rate=self.sample_rate
            )
            
            samples = []
            for frame in container.decode(audio=0):
                resampled_frames = resampler.resample(frame)
                for r_frame in resampled_frames:
                    arr = r_frame.to_ndarray()
                    samples.append(arr.flatten())
                    
            if not samples:
                return np.zeros(0, dtype=np.float32)
                
            return np.concatenate(samples)
        except Exception as e:
            log.warning("asr_decode_failed", err=str(e))
            return np.zeros(0, dtype=np.float32)

    async def process_stream(self, audio_queue: asyncio.Queue) -> AsyncGenerator[dict, None]:
        """
        Consumes bytes from audio_queue and yields transcription segments.
        Because faster-whisper is not truly streaming chunk-by-chunk by default,
        we buffer audio and transcribe it in sliding windows for this prototype.
        """
        await self._ensure_model()
        if not self.model:
            yield {"type": "asr_error", "message": "ASR engine unavailable"}
            return

        buffer = np.zeros(0, dtype=np.float32)
        accumulated_text = ""
        start_time = time.time()
        
        webm_buffer = bytearray()
        decoded_audio_len = 0
        
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                # End of stream
                break
                
            webm_buffer.extend(chunk)
                
            # Decode the entire incoming stream so far
            full_audio = await asyncio.to_thread(self._decode_audio_chunk, bytes(webm_buffer))
            if len(full_audio) == 0 or len(full_audio) <= decoded_audio_len:
                continue
                
            decoded_chunk = full_audio[decoded_audio_len:]
            decoded_audio_len = len(full_audio)
            
            buffer = np.concatenate((buffer, decoded_chunk))
            
            # If buffer is >= 2 seconds, transcribe
            if len(buffer) >= self.sample_rate * 2:
                # Transcribe
                segments, info = await asyncio.to_thread(
                    self.model.transcribe,
                    buffer,
                    beam_size=1,
                    language="en",
                    vad_filter=True,
                )
                
                text = " ".join([segment.text for segment in segments])
                if text.strip():
                    yield {
                        "type": "asr_partial",
                        "text": text.strip()
                    }
                    
                if len(buffer) > self.sample_rate * 10:
                    accumulated_text += " " + text
                    
                    # Phase 26: Diarize the final segment
                    global_start_time = max(0.0, time.time() - start_time - (len(buffer) / self.sample_rate))
                    whisper_segments_dicts = [
                        {"start": s.start, "end": s.end, "text": s.text} 
                        for s in segments
                    ]
                    
                    diarized_segments = default_diarization_provider.diarize(
                        audio_buffer=buffer,
                        sample_rate=self.sample_rate,
                        whisper_segments=whisper_segments_dicts,
                        global_start_time=global_start_time
                    )                    
                    yield {
                        "type": "asr_final",
                        "text": accumulated_text.strip(),
                        "diarization": [s.model_dump() for s in diarized_segments]
                    }
                    buffer = np.zeros(0, dtype=np.float32)

# Global singleton
asr_service = ASRService()
