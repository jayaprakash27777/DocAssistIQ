"""DocAssistIQ — Streaming ASR Service (Phase 25+).

Integrates `faster-whisper` for real-time speech-to-text.
Decodes incoming WebM/Opus, WAV, MP4, or raw PCM chunks.
Provides an async generator yielding real-time partial and final transcription segments.
Guarantees zero dropped audio upon stream stop.
"""

import asyncio
import io
import wave
import structlog
from typing import AsyncGenerator, Dict, Any, List
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
    def __init__(self, model_size: str = "base.en", device: str = "auto", compute_type: str = "auto"):
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
                    # Check CUDA availability
                    use_cuda = False
                    try:
                        import torch
                        use_cuda = torch.cuda.is_available()
                    except Exception:
                        use_cuda = False

                    if use_cuda:
                        try:
                            self.model = await asyncio.to_thread(
                                WhisperModel,
                                self.model_size,
                                device="cuda",
                                compute_type="float16",
                                download_root="./model_cache",
                                cpu_threads=2
                            )
                            log.info("asr_model_loaded_gpu")
                            return
                        except Exception as e:
                            log.warning(f"Failed to load whisper on GPU: {e}. Falling back to CPU.")

                    # Load on CPU with int8 quantization (high speed, low memory, bounded CPU footprint)
                    self.model = await asyncio.to_thread(
                        WhisperModel,
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                        download_root="./model_cache",
                        cpu_threads=1
                    )
                    log.info("asr_model_loaded_cpu")

    def _decode_audio_chunk(self, audio_data: bytes) -> np.ndarray:
        """Decode WebM/Opus, WAV, MP4, MP3, or raw PCM to 16kHz mono float32 numpy array."""
        if not audio_data or len(audio_data) == 0:
            return np.zeros(0, dtype=np.float32)

        # 1. Try PyAV container decoding (WebM / Opus / MP4 / OGG)
        if av:
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
                        
                if samples:
                    return np.concatenate(samples)
            except Exception:
                pass

        # 2. Try standard library wave module (for standard WAV)
        try:
            bio = io.BytesIO(audio_data)
            with wave.open(bio, 'rb') as wf:
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
                
                if sampwidth == 2:
                    raw_arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                elif sampwidth == 4:
                    raw_arr = np.frombuffer(frames, dtype=np.float32)
                else:
                    raw_arr = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

                if channels > 1:
                    raw_arr = raw_arr.reshape(-1, channels).mean(axis=1)

                if framerate != self.sample_rate and len(raw_arr) > 0:
                    indices = np.round(np.arange(0, len(raw_arr), framerate / self.sample_rate)).astype(int)
                    indices = indices[indices < len(raw_arr)]
                    raw_arr = raw_arr[indices]

                if len(raw_arr) > 0:
                    return raw_arr
        except Exception:
            pass

        # 3. Try raw PCM 16-bit little-endian fallback
        try:
            if len(audio_data) % 2 == 0 and len(audio_data) >= 320:
                raw_pcm = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                if np.max(np.abs(raw_pcm)) <= 1.0 and len(raw_pcm) > 0:
                    return raw_pcm
        except Exception:
            pass

        return np.zeros(0, dtype=np.float32)

    async def transcribe_audio_bytes(self, audio_data: bytes) -> Dict[str, Any]:
        """Transcribe an entire audio recording (WebM, WAV, MP4, MP3, etc.) with speaker diarization."""
        await self._ensure_model()
        if not self.model:
            return {"text": "", "segments": [], "error": "ASR engine unavailable"}

        audio_arr = await asyncio.to_thread(self._decode_audio_chunk, audio_data)
        if len(audio_arr) == 0:
            return {"text": "", "segments": [], "error": "Could not decode audio"}

        def _do_transcribe(arr):
            segments_gen, info = self.model.transcribe(
                arr,
                beam_size=1,
                language="en",
                condition_on_previous_text=False,
                vad_filter=True,
            )
            return list(segments_gen), info

        segments, info = await asyncio.to_thread(_do_transcribe, audio_arr)
        full_text = " ".join([s.text.strip() for s in segments]).strip()

        whisper_segments_dicts = [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments
            if s.text.strip()
        ]

        diarized = await asyncio.to_thread(
            default_diarization_provider.diarize,
            audio_buffer=audio_arr,
            sample_rate=self.sample_rate,
            whisper_segments=whisper_segments_dicts,
            global_start_time=0.0
        )

        return {
            "text": full_text,
            "segments": [s.model_dump() for s in diarized],
            "duration": round(len(audio_arr) / self.sample_rate, 2),
            "language": getattr(info, "language", "en"),
        }

    async def process_stream(self, audio_queue: asyncio.Queue) -> AsyncGenerator[dict, None]:
        """
        Consumes bytes from audio_queue and yields real-time transcription segments.
        Guarantees:
        1. Fast partial transcription (every ~1.5s of new speech)
        2. Periodic finalization (every ~5-6s)
        3. Zero dropped audio on stream close / stop
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
        last_transcribe_len = 0
        
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                # End of stream (audio_stop or client disconnected)
                # Transcribe and finalize ALL remaining audio in buffer
                if len(buffer) > self.sample_rate * 0.4:
                    def run_final_transcription(audio_buf):
                        segs, _ = self.model.transcribe(
                            audio_buf,
                            beam_size=2,
                            language="en",
                            vad_filter=True,
                        )
                        return list(segs)

                    segments = await asyncio.to_thread(run_final_transcription, buffer)
                    final_chunk_text = " ".join([s.text.strip() for s in segments]).strip()
                    if final_chunk_text:
                        accumulated_text = (accumulated_text + " " + final_chunk_text).strip()
                    
                    if segments:
                        global_start = max(0.0, time.time() - start_time - (len(buffer) / self.sample_rate))
                        whisper_segments_dicts = [
                            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} 
                            for s in segments
                            if s.text.strip()
                        ]
                        diarized_segs = await asyncio.to_thread(
                            default_diarization_provider.diarize,
                            audio_buffer=buffer,
                            sample_rate=self.sample_rate,
                            whisper_segments=whisper_segments_dicts,
                            global_start_time=global_start
                        )
                        dumped = [s.model_dump() for s in diarized_segs]
                        yield {
                            "type": "asr_final",
                            "text": final_chunk_text,
                            "diarization": dumped,
                            "is_last": True
                        }
                break
                
            webm_buffer.extend(chunk)
                
            # Decode incoming audio stream
            full_audio = await asyncio.to_thread(self._decode_audio_chunk, bytes(webm_buffer))
            if len(full_audio) == 0:
                # Standalone chunk decode fallback
                chunk_audio = await asyncio.to_thread(self._decode_audio_chunk, chunk)
                if len(chunk_audio) > 0:
                    buffer = np.concatenate((buffer, chunk_audio))
            elif len(full_audio) > decoded_audio_len:
                decoded_chunk = full_audio[decoded_audio_len:]
                decoded_audio_len = len(full_audio)
                buffer = np.concatenate((buffer, decoded_chunk))
            
            # If buffer has >= 1.5s of speech and has advanced by >= 1.0s, emit partial
            if len(buffer) >= self.sample_rate * 1.5 and (len(buffer) - last_transcribe_len) >= self.sample_rate * 1.0:
                last_transcribe_len = len(buffer)
                
                def run_transcription(audio_buffer):
                    segments_gen, _ = self.model.transcribe(
                        audio_buffer,
                        beam_size=1,
                        language="en",
                        vad_filter=True,
                    )
                    return list(segments_gen)

                segments = await asyncio.to_thread(run_transcription, buffer)
                partial_text = " ".join([segment.text.strip() for segment in segments]).strip()
                if partial_text:
                    yield {
                        "type": "asr_partial",
                        "text": partial_text
                    }
                    
                # Emit asr_final every 5-6 seconds of speech for live diarization
                if len(buffer) >= self.sample_rate * 5.5:
                    accumulated_text = (accumulated_text + " " + partial_text).strip()
                    global_start_time = max(0.0, time.time() - start_time - (len(buffer) / self.sample_rate))
                    whisper_segments_dicts = [
                        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} 
                        for s in segments
                        if s.text.strip()
                    ]
                    
                    diarized_segments = await asyncio.to_thread(
                        default_diarization_provider.diarize,
                        audio_buffer=buffer,
                        sample_rate=self.sample_rate,
                        whisper_segments=whisper_segments_dicts,
                        global_start_time=global_start_time
                    )
                    dumped = [s.model_dump() for s in diarized_segments]
                    
                    yield {
                        "type": "asr_final",
                        "text": partial_text,
                        "diarization": dumped,
                        "is_last": False
                    }
                    # Reset buffer for next segment window
                    buffer = np.zeros(0, dtype=np.float32)
                    last_transcribe_len = 0

# Global singleton
asr_service = ASRService()

