"""DocAssistIQ — Speaker Diarization Provider (Phase 26)."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

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
    def diarize_segment(self, text: str, start: float, end: float) -> List[TranscriptSegment]:
        """Apply speaker diarization to a raw transcript segment."""
        pass


class HeuristicDiarizationProvider(SpeakerDiarizationProvider):
    """
    Fallback provider when real acoustic diarization is unavailable.
    Uses heuristic rule-based turns (e.g. question mark detection)
    but explicitly exposes low confidence to the UI.
    """
    
    def diarize_segment(self, text: str, start: float, end: float) -> List[TranscriptSegment]:
        if not text.strip():
            return []
            
        # Very naive heuristic: sentences ending in '?' might be the clinician asking.
        # This is purely fallback/heuristic if no real model is present.
        segments = []
        is_question = text.strip().endswith('?')
        
        segments.append(TranscriptSegment(
            speaker="Unknown" if not is_question else "Likely Doctor",
            start=start,
            end=end,
            text=text.strip(),
            confidence=0.3,  # Explicitly expose high uncertainty for heuristic
            source="heuristic"
        ))
        
        return segments


class RealDiarizationProvider(SpeakerDiarizationProvider):
    """
    Placeholder for actual acoustic diarization (e.g. pyannote.audio).
    Not loaded by default due to heavy ML requirements.
    """
    def diarize_segment(self, text: str, start: float, end: float) -> List[TranscriptSegment]:
        raise NotImplementedError("Real diarization requires pyannote.audio")


# Injectable default
default_diarization_provider = HeuristicDiarizationProvider()
