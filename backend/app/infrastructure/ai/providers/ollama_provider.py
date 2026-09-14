"""DocAssistIQ — Ollama AI Providers (Offline, Free).

Implementations of AI Provider interfaces using local Ollama instances.
"""

import json
from typing import Any
import httpx

from app.infrastructure.ai.interfaces import (
    AIProviderMetadata,
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
    EmbeddingProvider,
)


class OllamaGenerationProvider(GenerationProvider):
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Local Ollama",
            model_name=self.model_name,
            version="1.0",
            capabilities=["text-generation", "json-mode"],
        )

    async def generate(self, request: GenerationRequest, timeout: float | None = None) -> GenerationResult:
        payload = {
            "model": self.model_name,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
            }
        }
        
        if request.system_prompt:
            payload["system"] = request.system_prompt
            
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens  # type: ignore

        if request.json_schema:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=timeout or 60.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return GenerationResult(
                text=data.get("response", ""),
                finish_reason="stop",
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
            )


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = "http://localhost:11434", dimensions: int = 768):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.dimensions = dimensions

    @property
    def metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="Local Ollama Embeddings",
            model_name=self.model_name,
            version="1.0",
            capabilities=["text-embedding"],
        )

    async def embed(self, text: str, timeout: float | None = None) -> list[float]:
        async with httpx.AsyncClient(timeout=timeout or 60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            
            emb = data.get("embedding", [])
            if not emb:
                raise ValueError("No embeddings returned from Ollama API")
                
            return emb
