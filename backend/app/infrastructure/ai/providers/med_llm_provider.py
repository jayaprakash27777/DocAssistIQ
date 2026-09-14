"""DocAssistIQ ?" Medical LLM Provider (Phase 62).

Implements the DiagnosisProvider using local Foundation Models (e.g., Llama 3.2 via Ollama)
kept strictly in evaluation/research mode.
"""

import json
from typing import Any
import httpx

from app.infrastructure.ai.interfaces import (
    AIProviderMetadata,
    DiagnosisProvider,
    DiagnosisHypothesis,
)


class LocalMedicalLLMProvider(DiagnosisProvider):
    """
    Local Medical Foundation Model provider using Ollama.
    
    WARNING: This provider must remain in `is_research_mode=True` until clinical gating
    and rigorous safety evaluations pass.
    """
    def __init__(
        self, 
        model_name: str = "llama3.2:latest", 
        base_url: str = "http://localhost:11434",
        is_research_mode: bool = True
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        
        # Enforce clinical gating requirements (Phase 62)
        if not is_research_mode:
            raise RuntimeError(
                "Clinical Gating Violation: Local Medical LLM has not passed safety review. "
                "It can only be instantiated with `is_research_mode=True`."
            )
        self.is_research_mode = True

    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Local Medical LLM (Ollama)",
            model_name=self.model_name,
            version="1.0",
            capabilities=["clinical-reasoning", "differential-diagnosis"],
        )

    async def suggest_diagnoses(
        self, clinical_history: str, findings: list[str], timeout: float | None = None
    ) -> list[DiagnosisHypothesis]:
        """
        Queries the local Foundation Model to generate diagnostic hypotheses based on 
        the presentation. Parses the JSON structure.
        """
        system_prompt = (
            "You are an expert clinical diagnostician AI. "
            "Given the clinical history and findings, provide a differential diagnosis. "
            "Output strictly valid JSON as a list of objects with the following keys: "
            "'condition_code' (ICD-10 or SNOMED-like code), 'condition_name', "
            "'probability' (float between 0 and 1), 'rationale' (string), "
            "and 'supporting_evidence' (list of strings)."
        )
        
        user_prompt = f"Clinical History: {clinical_history}\nFindings: {', '.join(findings)}"
        
        payload = {
            "model": self.model_name,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,  # Low temperature for clinical tasks
            }
        }
        
        async with httpx.AsyncClient(timeout=timeout or 120.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            
            raw_response = data.get("response", "[]")
            try:
                parsed_json = json.loads(raw_response)
                # If it returned a dict with a list inside, try to extract it
                if isinstance(parsed_json, dict) and len(parsed_json.keys()) == 1:
                    parsed_json = list(parsed_json.values())[0]
                    
                if not isinstance(parsed_json, list):
                    parsed_json = [parsed_json]
                    
                hypotheses = []
                for item in parsed_json:
                    hypotheses.append(DiagnosisHypothesis(
                        condition_code=item.get("condition_code", "UNKNOWN"),
                        condition_name=item.get("condition_name", "Unknown Condition"),
                        probability=float(item.get("probability", 0.0)),
                        rationale=item.get("rationale", ""),
                        supporting_evidence=item.get("supporting_evidence", [])
                    ))
                return hypotheses
            except json.JSONDecodeError:
                raise ValueError("Model did not return valid JSON.")
