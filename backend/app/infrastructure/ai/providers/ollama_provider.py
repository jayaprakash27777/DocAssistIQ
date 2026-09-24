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
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
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

        gen_timeout = timeout or 30.0
        client_timeout = httpx.Timeout(connect=3.0, read=gen_timeout, write=10.0, pool=3.0)
        try:
            async with self._client if hasattr(self, '_client') else httpx.AsyncClient(timeout=client_timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                raw_text = data.get("response", "").strip()
                import re
                if "</think>" in raw_text:
                    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw_text).strip()
                    final_text = cleaned if cleaned else re.sub(r"<think>([\s\S]*?)</think>", r"\1", raw_text).strip()
                elif raw_text.startswith("<think>"):
                    final_text = re.sub(r"^<think>\s*", "", raw_text).strip()
                else:
                    final_text = raw_text
                
                return GenerationResult(
                    text=final_text,
                    finish_reason="stop",
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    },
                )
        except Exception:
            from app.infrastructure.ai.providers.baseline import BaselineGenerationProvider
            return await BaselineGenerationProvider().generate(request, timeout=timeout)


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
        emb_timeout = timeout or 15.0
        client_timeout = httpx.Timeout(connect=3.0, read=emb_timeout, write=5.0, pool=3.0)
        try:
            async with httpx.AsyncClient(timeout=client_timeout) as client:
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
        except Exception:
            # Deterministic, normalized fallback embedding vector matching target dimensions
            import hashlib
            h = hashlib.sha256(text.encode("utf-8")).digest()
            return [(h[i % len(h)] / 255.0) - 0.5 for i in range(self.dimensions)]
