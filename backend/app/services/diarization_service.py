"""DocAssistIQ — Speaker Diarization Provider (Phase 26)."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import structlog
import numpy as np

log = structlog.get_logger(__name__)

class TranscriptSegment(BaseModel):
    speaker: Optional[str] = Field(None, description="e.g. 'Speaker 1', 'Doctor', 'Patient'")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Confidence score 0.0 - 1.0")
    source: str = Field(..., description="'asr', 'diarization', 'heuristic'")


class SpeakerDiarizationProvider(ABC):
    """Abstract capability for speaker attribution."""
    
    @abstractmethod
    def diarize(self, audio_buffer: np.ndarray, sample_rate: int, whisper_segments: List[Dict[str, Any]], global_start_time: float) -> List[TranscriptSegment]:
        """Apply speaker diarization to an acoustic buffer and align with text segments."""
        pass


class HeuristicDiarizationProvider(SpeakerDiarizationProvider):
    """
    Fallback provider when real acoustic diarization is unavailable.
    Uses heuristic rule-based turns (e.g. question mark detection)
    but explicitly exposes low confidence to the UI.
    """
    
    def diarize(self, audio_buffer: np.ndarray, sample_rate: int, whisper_segments: List[Dict[str, Any]], global_start_time: float) -> List[TranscriptSegment]:
        results = []
        for seg in whisper_segments:
            text = seg.get("text", "")
            start = seg.get("start", 0.0) + global_start_time
            end = seg.get("end", 0.0) + global_start_time
            
            if not text.strip():
                continue
                
            is_question = text.strip().endswith('?')
            results.append(TranscriptSegment(
                speaker="Unknown" if not is_question else "Likely Doctor",
                start=start,
                end=end,
                text=text.strip(),
                confidence=0.3,
                source="heuristic"
            ))
        return results


class RealDiarizationProvider(SpeakerDiarizationProvider):
    """
    Acoustic diarization using pyannote.audio.
    Dynamically loads dependencies and falls back to heuristic if unavailable.
    """
    def __init__(self):
        self._pipeline = None
        self._load_attempted = False

    def _ensure_pipeline(self):
        if self._load_attempted:
            return
        self._load_attempted = True
        try:
            import torch
            from pyannote.audio import Pipeline
            from app.config import get_settings
            
            settings = get_settings()
            if not settings.hf_token:
                log.warning("HF_TOKEN not set. Pyannote diarization unavailable. Falling back to heuristic.")
                return
                
            log.info("Loading pyannote speaker diarization pipeline...")
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=settings.hf_token
            )
            # Use GPU if available
            if torch.cuda.is_available():
                self._pipeline.to(torch.device("cuda"))
            log.info("Pyannote pipeline loaded successfully.")
        except ImportError as e:
            log.warning(f"Pyannote/Torch not installed: {e}. Falling back to heuristic diarization.")
        except Exception as e:
            log.warning(f"Failed to load Pyannote pipeline: {e}. Falling back to heuristic.")

    def diarize(self, audio_buffer: np.ndarray, sample_rate: int, whisper_segments: List[Dict[str, Any]], global_start_time: float) -> List[TranscriptSegment]:
        self._ensure_pipeline()
        
        # If pipeline failed to load or no HF_TOKEN, gracefully fallback to heuristic
        if not self._pipeline:
            fallback = HeuristicDiarizationProvider()
            return fallback.diarize(audio_buffer, sample_rate, whisper_segments, global_start_time)
            
        try:
            import torch
            # Pyannote expects a torch tensor of shape (channels, samples)
            waveform = torch.from_numpy(audio_buffer).unsqueeze(0).float()
            # Pyannote pipeline requires a dict with waveform and sample_rate
            diarization = self._pipeline({"waveform": waveform, "sample_rate": sample_rate})
            
            # Intersection logic: assign each whisper segment to the speaker who spoke the most during its timeframe
            results = []
            for seg in whisper_segments:
                seg_start = seg.get("start", 0.0)
                seg_end = seg.get("end", 0.0)
                text = seg.get("text", "")
                
                # Find the intersection of this text segment with the diarization outputs
                best_speaker = "Unknown"
                max_overlap = 0.0
                
                # diarization.itertracks(yield_label=True) yields (segment, track, label)
                for turn, _, speaker_label in diarization.itertracks(yield_label=True):
                    # Calculate overlap between Whisper text segment and Pyannote speaker segment
                    overlap_start = max(seg_start, turn.start)
                    overlap_end = min(seg_end, turn.end)
                    overlap_duration = max(0.0, overlap_end - overlap_start)
                    
                    if overlap_duration > max_overlap:
                        max_overlap = overlap_duration
                        best_speaker = speaker_label
                        
                results.append(TranscriptSegment(
                    speaker=best_speaker,
                    start=seg_start + global_start_time,
                    end=seg_end + global_start_time,
                    text=text.strip(),
                    confidence=0.85, # Real acoustic diarization confidence
                    source="diarization"
                ))
            return results
        except Exception as e:
            log.error(f"Pyannote execution failed: {e}. Falling back to heuristic.")
            fallback = HeuristicDiarizationProvider()
            return fallback.diarize(audio_buffer, sample_rate, whisper_segments, global_start_time)


# Injectable default - attempt to use Real, gracefully fallback to Heuristic
default_diarization_provider = RealDiarizationProvider()
