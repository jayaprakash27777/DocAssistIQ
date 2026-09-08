"""DocAssistIQ — Baseline AI Providers (Phase 16).

Lightweight implementations suitable for development and testing
without requiring large external model downloads or expensive API keys.
"""

import asyncio
from typing import Any

from app.infrastructure.ai.interfaces import (
    AIProviderMetadata,
    ExtractedEntity,
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
    MedicalNLPProvider,
    SpeechToTextProvider,
    SpeechToTextResult,
    SpeakerDiarizationProvider,
    SpeakerSegment,
    EmbeddingProvider,
    RerankerProvider,
    RerankResult,
    DiagnosisProvider,
    DiagnosisHypothesis,
    OCRProvider,
    OCRResult,
    VisionProvider,
)


class BaselineGenerationProvider(GenerationProvider):
    """A dummy generation provider that returns mocked responses."""
    
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-llm-v1",
            version="1.0",
            capabilities=["text-generation", "json-mode"],
        )

    async def generate(self, request: GenerationRequest, timeout: float | None = None) -> GenerationResult:
        await asyncio.sleep(0.5)  # Simulate network/processing latency
        
        # Simple mock behavior based on prompt content
        text = "This is a baseline generated response based on the prompt."
        if "summary" in request.prompt.lower():
            text = "Patient presented with typical symptoms. Advised rest and hydration."
            
        if request.json_schema:
            text = '{"status": "mocked", "result": "success"}'
            
        return GenerationResult(
            text=text,
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
        )


class BaselineMedicalNLPProvider(MedicalNLPProvider):
    """A dummy NLP provider that extracts static entities using simple heuristics."""
    
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-ner-v1",
            version="1.0",
            capabilities=["entity-extraction"],
        )

    async def extract_entities(self, text: str, timeout: float | None = None) -> list[ExtractedEntity]:
        await asyncio.sleep(0.2)
        entities = []
        text_lower = text.lower()
        
        # Extremely basic mock heuristic for demonstration
        if "headache" in text_lower:
            entities.append(ExtractedEntity(
                entity_type="symptom", text="headache", canonical_code="SNOMED:25064002", confidence=0.95
            ))
        if "paracetamol" in text_lower or "tylenol" in text_lower:
            entities.append(ExtractedEntity(
                entity_type="medicine", text="paracetamol", canonical_code="RxNorm:161", confidence=0.99
            ))
        if "hypertension" in text_lower:
             entities.append(ExtractedEntity(
                entity_type="disease", text="hypertension", canonical_code="ICD10:I10", confidence=0.90
            ))
             
        return entities


class BaselineSpeechToTextProvider(SpeechToTextProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-stt-v1",
            version="1.0",
            capabilities=["speech-to-text"],
        )

    async def transcribe(self, audio_bytes: bytes, mime_type: str, timeout: float | None = None) -> SpeechToTextResult:
        await asyncio.sleep(0.5)
        return SpeechToTextResult(
            text="Patient reports a mild headache since yesterday.",
            confidence=0.92,
            language="en"
        )


class BaselineSpeakerDiarizationProvider(SpeakerDiarizationProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-diarization-v1",
            version="1.0",
            capabilities=["speaker-diarization"],
        )

    async def diarize(self, audio_bytes: bytes, mime_type: str, transcript: str | None = None, timeout: float | None = None) -> list[SpeakerSegment]:
        await asyncio.sleep(0.5)
        return [
            SpeakerSegment(speaker_id="SPEAKER_00", start_time=0.0, end_time=2.0, text="How are you feeling?"),
            SpeakerSegment(speaker_id="SPEAKER_01", start_time=2.1, end_time=5.0, text="I have a mild headache."),
        ]


class BaselineEmbeddingProvider(EmbeddingProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-embed-v1",
            version="1.0",
            capabilities=["text-embedding"],
        )

    async def embed(self, text: str, timeout: float | None = None) -> list[float]:
        await asyncio.sleep(0.1)
        # Return a dummy 384-dimensional vector
        return [0.01] * 384


class BaselineRerankerProvider(RerankerProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-rerank-v1",
            version="1.0",
            capabilities=["document-reranking"],
        )

    async def rerank(self, query: str, documents: list[str], top_k: int = 5, timeout: float | None = None) -> list[RerankResult]:
        await asyncio.sleep(0.2)
        # Simply return them in original order with fake scores
        return [
            RerankResult(index=i, score=0.9 - (i * 0.1), text=doc)
            for i, doc in enumerate(documents[:top_k])
        ]


class BaselineDiagnosisProvider(DiagnosisProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-diagnosis-v1",
            version="1.0",
            capabilities=["differential-diagnosis"],
        )

    async def suggest_diagnoses(self, clinical_history: str, findings: list[str], timeout: float | None = None) -> list[DiagnosisHypothesis]:
        await asyncio.sleep(0.5)
        return [
            DiagnosisHypothesis(
                condition_code="ICD10:J06.9",
                condition_name="Acute upper respiratory infection",
                probability=0.85,
                rationale="Presence of cough and mild fever.",
                supporting_evidence=["symptom:cough", "sign:fever"]
            )
        ]


class BaselineOCRProvider(OCRProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-ocr-v1",
            version="1.0",
            capabilities=["ocr"],
        )

    async def extract_text(self, image_bytes: bytes, mime_type: str, timeout: float | None = None) -> OCRResult:
        await asyncio.sleep(0.5)
        return OCRResult(
            text="Laboratory Results: Hemoglobin 14.2 g/dL",
            confidence=0.98,
        )


class BaselineVisionProvider(VisionProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="mock-vision-v1",
            version="1.0",
            capabilities=["image-analysis"],
        )

    async def analyze_image(self, image_bytes: bytes, mime_type: str, prompt: str, timeout: float | None = None) -> str:
        await asyncio.sleep(0.8)
        return "Image shows no acute cardiopulmonary abnormalities."
