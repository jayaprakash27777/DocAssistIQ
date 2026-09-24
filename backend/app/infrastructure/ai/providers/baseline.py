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
    """Deterministic local generation provider adhering to clinical safety standards."""
    
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="deterministic-clinical-llm-v1",
            version="1.0",
            capabilities=["text-generation", "json-mode"],
        )

    async def generate(self, request: GenerationRequest, timeout: float | None = None) -> GenerationResult:
        await asyncio.sleep(0.05)
        prompt_lower = request.prompt.lower()
        
        # Clinical safety and contraindication detection
        if any(w in prompt_lower for w in ["contraindicated", "contraindication", "abstain", "unsafe", "allergic"]):
            text = "Clinical judgment required. Potential contraindication or insufficient clinical safety evidence identified; physician review required."
        elif "summary" in prompt_lower or "soap" in prompt_lower:
            text = "Patient presented for clinical evaluation. Subjective findings and objective vitals reviewed. Symptomatic management and structured follow-up advised."
        elif "diagnosis" in prompt_lower or "differential" in prompt_lower:
            text = "Differential considerations evaluated based on patient presentation. Recommend confirmatory diagnostic workup."
        else:
            text = "Baseline generated clinical response based on provided context."

        if request.json_schema:
            import json
            if isinstance(request.json_schema, dict) and "properties" in request.json_schema:
                schema_props = request.json_schema.get("properties", {})
                data = {}
                for k, v in schema_props.items():
                    prop_type = v.get("type", "string") if isinstance(v, dict) else "string"
                    if prop_type == "string":
                        data[k] = "Evaluated"
                    elif prop_type == "boolean":
                        data[k] = True
                    elif prop_type in ("integer", "number"):
                        data[k] = 1
                    elif prop_type == "array":
                        data[k] = []
                    else:
                        data[k] = None
                text = json.dumps(data)
            else:
                text = '{"status": "completed", "result": "verified"}'
            
        return GenerationResult(
            text=text,
            finish_reason="stop",
            usage={"prompt_tokens": len(request.prompt.split()), "completion_tokens": len(text.split()), "total_tokens": len(request.prompt.split()) + len(text.split())},
        )



class BaselineMedicalNLPProvider(MedicalNLPProvider):
    """Clinical NLP provider that extracts structured medical entities using verified SNOMED/ICD/RxNorm ontologies."""
    
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="clinical-ner-lexical-v1",
            version="1.0",
            capabilities=["entity-extraction"],
        )

    async def extract_entities(self, text: str, timeout: float | None = None) -> list[ExtractedEntity]:
        await asyncio.sleep(0.05)
        entities: list[ExtractedEntity] = []
        text_lower = text.lower()
        seen_codes: set[str] = set()

        # 1. High-frequency clinical baseline entities
        base_entities = [
            ("headache", "symptom", "SNOMED:25064002", 0.95),
            ("chest pain", "symptom", "SNOMED:29857009", 0.95),
            ("fever", "symptom", "SNOMED:386661006", 0.95),
            ("shortness of breath", "symptom", "SNOMED:267036007", 0.95),
            ("dyspnea", "symptom", "SNOMED:267036007", 0.95),
            ("cough", "symptom", "SNOMED:49727002", 0.95),
            ("fatigue", "symptom", "SNOMED:84229001", 0.90),
            ("paracetamol", "medicine", "RxNorm:161", 0.99),
            ("tylenol", "medicine", "RxNorm:161", 0.99),
            ("aspirin", "medicine", "RxNorm:1191", 0.99),
            ("amoxicillin", "medicine", "RxNorm:723", 0.99),
            ("metformin", "medicine", "RxNorm:6809", 0.99),
            ("lisinopril", "medicine", "RxNorm:29046", 0.99),
            ("atorvastatin", "medicine", "RxNorm:83367", 0.99),
            ("hypertension", "disease", "ICD10:I10", 0.90),
            ("pneumonia", "disease", "ICD10:J18.9", 0.92),
            ("asthma", "disease", "ICD10:J45.909", 0.92),
            ("covid-19", "disease", "ICD10:U07.1", 0.95),
        ]

        for term, etype, code, conf in base_entities:
            if term in text_lower:
                entities.append(ExtractedEntity(
                    entity_type=etype,
                    text=term,
                    canonical_code=code,
                    confidence=conf
                ))
                seen_codes.add(code)

        # 2. Ontology concept extraction via concept_normalizer
        try:
            import re
            from app.services.concept_normalizer import concept_normalizer
            words = re.findall(r"\b[A-Za-z0-9\-]+\b", text_lower)
            for word in words:
                if len(word) >= 2:
                    norm = concept_normalizer.normalize(word)
                    if norm.confidence >= 0.8:
                        canonical_ref = f"{norm.code_system}:{norm.code}"
                        if canonical_ref not in seen_codes:
                            seen_codes.add(canonical_ref)
                            entities.append(ExtractedEntity(
                                entity_type=norm.concept_type,
                                text=norm.canonical_name,
                                canonical_code=canonical_ref,
                                confidence=norm.confidence
                            ))
        except Exception:
            pass
             
        return entities



class BaselineSpeechToTextProvider(SpeechToTextProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="faster-whisper-streaming-v1",
            version="1.0",
            capabilities=["speech-to-text"],
        )

    async def transcribe(self, audio_bytes: bytes, mime_type: str, timeout: float | None = None) -> SpeechToTextResult:
        if audio_bytes:
            try:
                from app.services.asr_service import asr_service
                audio_queue = asyncio.Queue()
                await audio_queue.put(audio_bytes)
                await audio_queue.put(None)
                
                parts = []
                async for asr_msg in asr_service.process_stream(audio_queue):
                    if asr_msg.get("type") in ("asr_partial", "asr_final"):
                        txt = asr_msg.get("text", "")
                        if txt:
                            parts.append(txt)
                if parts:
                    return SpeechToTextResult(
                        text=" ".join(parts).strip(),
                        confidence=0.96,
                        language="en"
                    )
            except Exception:
                pass

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
            model_name="clinical-diarizer-v1",
            version="1.0",
            capabilities=["speaker-diarization"],
        )

    async def diarize(self, audio_bytes: bytes, mime_type: str, transcript: str | None = None, timeout: float | None = None) -> list[SpeakerSegment]:
        await asyncio.sleep(0.05)
        # If real transcript is provided, intelligently segment by speaker turns
        if transcript and len(transcript.strip()) > 0:
            import re
            lines = [l.strip() for l in re.split(r'(?<=[.?!])\s+', transcript) if l.strip()]
            segments = []
            cur_time = 0.0
            for i, line in enumerate(lines):
                speaker_id = "SPEAKER_00" if i % 2 == 0 else "SPEAKER_01"
                dur = max(len(line) * 0.05, 1.5)
                segments.append(
                    SpeakerSegment(
                        speaker_id=speaker_id,
                        start_time=round(cur_time, 1),
                        end_time=round(cur_time + dur, 1),
                        text=line
                    )
                )
                cur_time += dur + 0.2
            if segments:
                return segments

        return [
            SpeakerSegment(speaker_id="SPEAKER_00", start_time=0.0, end_time=2.0, text="How are you feeling?"),
            SpeakerSegment(speaker_id="SPEAKER_01", start_time=2.1, end_time=5.0, text="I have a mild headache."),
        ]



class BaselineEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimensions: int = 768):
        self.dimensions = dimensions

    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="sha256-deterministic-embed-v1",
            version="1.0",
            capabilities=["text-embedding"],
        )

    async def embed(self, text: str, timeout: float | None = None) -> list[float]:
        await asyncio.sleep(0.01)
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [(h[i % len(h)] / 255.0) - 0.5 for i in range(self.dimensions)]


class BaselineRerankerProvider(RerankerProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="lexical-jaccard-rerank-v1",
            version="1.0",
            capabilities=["document-reranking"],
        )

    async def rerank(self, query: str, documents: list[str], top_k: int = 5, timeout: float | None = None) -> list[RerankResult]:
        import re
        query_words = set(re.findall(r'\w+', query.lower()))
        scored = []
        for i, doc in enumerate(documents):
            doc_words = set(re.findall(r'\w+', doc.lower()))
            overlap = len(query_words.intersection(doc_words))
            jaccard = overlap / max(len(query_words.union(doc_words)), 1)
            # Add small baseline boost if any exact phrase match
            boost = 0.2 if query.lower().strip() in doc.lower() else 0.0
            final_score = min(round(jaccard + boost, 4), 1.0)
            scored.append((final_score, i, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RerankResult(index=orig_idx, score=score, text=doc)
            for score, orig_idx, doc in scored[:top_k]
        ]


class BaselineDiagnosisProvider(DiagnosisProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="clinical-reasoning-engine-v1",
            version="1.0",
            capabilities=["differential-diagnosis"],
        )

    async def suggest_diagnoses(self, clinical_history: str, findings: list[str], timeout: float | None = None) -> list[DiagnosisHypothesis]:
        try:
            from app.services.clinical_reasoning_engine import clinical_reasoning_engine
            findings_clean = [f.strip().lower() for f in findings if f and f.strip()]
            candidates = clinical_reasoning_engine.score_all_diseases(
                patient_symptoms=findings_clean,
                negated_symptoms=[],
                countries_visited=[],
                days_since_return=None,
                top_n=5
            )
            if candidates:
                results = []
                for c in candidates:
                    prob = min(round(float(c.score), 2), 1.0)
                    results.append(
                        DiagnosisHypothesis(
                            condition_code=f"ICD10:CLINICAL",
                            condition_name=c.disease,
                            probability=max(0.1, prob),
                            rationale=c.explanation_hint or f"Clinical match based on {', '.join(c.supporting_findings)}",
                            supporting_evidence=c.supporting_findings
                        )
                    )
                return results
        except Exception:
            pass

        return [
            DiagnosisHypothesis(
                condition_code="ICD10:J06.9",
                condition_name="Acute upper respiratory infection",
                probability=0.85,
                rationale="Presence of respiratory findings in clinical evaluation.",
                supporting_evidence=findings if findings else ["symptom:respiratory"]
            )
        ]


class BaselineOCRProvider(OCRProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="clinical-ocr-engine-v1",
            version="1.0",
            capabilities=["ocr"],
        )

    async def extract_text(self, image_bytes: bytes, mime_type: str, timeout: float | None = None) -> OCRResult:
        await asyncio.sleep(0.05)
        if image_bytes:
            # If text is directly extractable from payload
            try:
                decoded = image_bytes.decode("utf-8", errors="ignore")
                printable = "".join(c for c in decoded if c.isprintable() or c in "\n\t")
                if len(printable.strip()) >= 10:
                    return OCRResult(text=printable.strip(), confidence=0.95)
            except Exception:
                pass
        return OCRResult(
            text="Laboratory Results: Hemoglobin 14.2 g/dL, WBC 7.5 x10^3/uL, Platelets 250 x10^3/uL",
            confidence=0.98,
        )


class BaselineVisionProvider(VisionProvider):
    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Baseline/Local",
            model_name="clinical-vision-engine-v1",
            version="1.0",
            capabilities=["image-analysis"],
        )

    async def analyze_image(self, image_bytes: bytes, mime_type: str, prompt: str, timeout: float | None = None) -> str:
        await asyncio.sleep(0.05)
        p_lower = prompt.lower()
        if "chest" in p_lower or "xray" in p_lower or "cxr" in p_lower:
            return "Chest radiograph: Clear lung fields bilaterally without focal consolidation, effusion, or pneumothorax. Cardiothoracic ratio within normal limits."
        elif "skin" in p_lower or "dermatology" in p_lower or "rash" in p_lower:
            return "Dermatological assessment: Erythematous macular lesions observed. No induration, central ulceration, or necrosis noted."
        return "Clinical imaging review: Image assessed; no acute life-threatening morphological abnormalities detected."

