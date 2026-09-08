"""DocAssistIQ — AI Provider Interfaces (Phase 16).

Strictly typed contracts for all AI operations.
Business logic must depend on these interfaces, not vendor-specific code.
"""

from abc import ABC, abstractmethod
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict


# ── Metadata Models ───────────────────────────────────────────

class AIProviderMetadata(BaseModel):
    """Metadata exposed by every provider implementation."""
    provider_name: str
    model_name: str
    version: str
    capabilities: list[str] = []
    
    model_config = ConfigDict(frozen=True)


# ── Base Interface ────────────────────────────────────────────

class AIProvider(ABC):
    """Base interface for all AI Providers."""
    
    @property
    @abstractmethod
    def metadata(self) -> AIProviderMetadata:
        """Get the provider's metadata (model name, capabilities)."""
        pass


# ── Speech Interfaces ─────────────────────────────────────────

class SpeechToTextResult(BaseModel):
    text: str
    confidence: float | None = None
    language: str | None = None


class SpeechToTextProvider(AIProvider):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, mime_type: str, timeout: float | None = None) -> SpeechToTextResult:
        """Transcribe audio bytes to text."""
        pass


class SpeakerSegment(BaseModel):
    speaker_id: str
    start_time: float
    end_time: float
    text: str


class SpeakerDiarizationProvider(AIProvider):
    @abstractmethod
    async def diarize(self, audio_bytes: bytes, mime_type: str, transcript: str | None = None, timeout: float | None = None) -> list[SpeakerSegment]:
        """Identify speakers and their speech segments."""
        pass


# ── NLP & Medical Interfaces ──────────────────────────────────

class ExtractedEntity(BaseModel):
    entity_type: Literal["symptom", "disease", "medicine", "investigation", "anatomy"]
    text: str
    canonical_code: str | None = None
    confidence: float


class MedicalNLPProvider(AIProvider):
    @abstractmethod
    async def extract_entities(self, text: str, timeout: float | None = None) -> list[ExtractedEntity]:
        """Extract medical entities from unstructured clinical text."""
        pass


class EmbeddingProvider(AIProvider):
    @abstractmethod
    async def embed(self, text: str, timeout: float | None = None) -> list[float]:
        """Generate a dense vector embedding for the text."""
        pass


class RerankResult(BaseModel):
    index: int
    score: float
    text: str


class RerankerProvider(AIProvider):
    @abstractmethod
    async def rerank(self, query: str, documents: list[str], top_k: int = 5, timeout: float | None = None) -> list[RerankResult]:
        """Rerank a list of documents against a query."""
        pass


# ── Generation Interfaces ─────────────────────────────────────

class GenerationRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None
    json_schema: dict | None = None


class GenerationResult(BaseModel):
    text: str
    finish_reason: str
    usage: dict[str, int]


class GenerationProvider(AIProvider):
    @abstractmethod
    async def generate(self, request: GenerationRequest, timeout: float | None = None) -> GenerationResult:
        """Generate text or JSON using an LLM."""
        pass


# ── Specialized Interfaces ────────────────────────────────────

class DiagnosisHypothesis(BaseModel):
    condition_code: str
    condition_name: str
    probability: float
    rationale: str
    supporting_evidence: list[str]


class DiagnosisProvider(AIProvider):
    @abstractmethod
    async def suggest_diagnoses(self, clinical_history: str, findings: list[str], timeout: float | None = None) -> list[DiagnosisHypothesis]:
        """Suggest differential diagnoses based on clinical presentation."""
        pass


class OCRResult(BaseModel):
    text: str
    confidence: float
    layout: dict | None = None


class OCRProvider(AIProvider):
    @abstractmethod
    async def extract_text(self, image_bytes: bytes, mime_type: str, timeout: float | None = None) -> OCRResult:
        """Extract text from clinical documents or scanned images."""
        pass


class VisionProvider(AIProvider):
    @abstractmethod
    async def analyze_image(self, image_bytes: bytes, mime_type: str, prompt: str, timeout: float | None = None) -> str:
        """Analyze medical imagery (x-rays, lesions) with VLM."""
        pass
