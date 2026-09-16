"""DocAssistIQ LLM Service — God-Level Upgrade.

Optimized for llama3.2 (3.2B params) on constrained hardware:
- Temperature = 0.0 for fully deterministic, reproducible output
- Token limits enforced (prevents runaway generation & RAM exhaustion)
- generate_narrator() — ultra-short prompt for 1-2 sentence explanations
- generate_json_compact() — enforces <600 token prompts
- Auto-retry with simplified prompt on failure
- Context window protection: truncates prompts exceeding 2000 chars
"""

import httpx
import json
import re
import structlog
from typing import Dict, Any, Optional

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt Safety Limits (for 3B model hardware constraint)
# ---------------------------------------------------------------------------
MAX_SYSTEM_PROMPT_CHARS = 1800   # ~450 tokens
MAX_USER_PROMPT_CHARS = 800      # ~200 tokens  
MAX_COMBINED_CHARS = 2400        # ~600 tokens total
MAX_TOKENS_JSON = 500            # Max output tokens for JSON
MAX_TOKENS_NARRATIVE = 200       # Max output tokens for narrative


def _truncate_prompt(text: str, max_chars: int) -> str:
    """Safely truncate a prompt to fit within token budget."""
    if len(text) <= max_chars:
        return text
    # Cut at last complete sentence/newline within budget
    truncated = text[:max_chars]
    last_newline = truncated.rfind("\n")
    if last_newline > max_chars * 0.7:
        return truncated[:last_newline] + "\n[...context truncated for hardware efficiency...]"
    return truncated + "...[truncated]"


class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
        self.default_model = "llama3.2"

    # ------------------------------------------------------------------
    # Core generation (unchanged — preserves all existing functionality)
    # ------------------------------------------------------------------

    async def generate(self, prompt: str, system: str = "", model: str | None = None) -> str:
        """Simple text generation using Ollama."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            log.error("ollama_generate_failed", error=str(e))
            raise e

    async def generate_json(self, prompt: str, system: str = "", model: str | None = None) -> Dict[str, Any]:
        """Generate guaranteed JSON output using Ollama's format=json parameter."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",
        }
        raw_response = "{}"
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "{}")
            json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw_response)
            clean_json = json_match.group(1) if json_match else raw_response
            return json.loads(clean_json)
        except Exception as e:
            log.error("ollama_generate_json_failed", error=str(e),
                      response_snippet=raw_response[:200])
            raise e

    # ------------------------------------------------------------------
    # NEW: Compact JSON — hardware-safe, enforces token budget
    # ------------------------------------------------------------------

    async def generate_json_compact(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_output_tokens: int = MAX_TOKENS_JSON,
    ) -> Dict[str, Any]:
        """
        Hardware-safe JSON generation.
        - Truncates system prompt to MAX_SYSTEM_PROMPT_CHARS
        - Truncates user prompt to MAX_USER_PROMPT_CHARS
        - Limits output tokens to max_output_tokens
        - Temperature = 0 for deterministic output
        - Auto-retries with even shorter prompt on failure

        Perfect for llama3.2 on 16GB RAM / RTX 3050.
        """
        target_model = model or self.default_model

        # Enforce token budget
        system_safe = _truncate_prompt(system, MAX_SYSTEM_PROMPT_CHARS)
        prompt_safe = _truncate_prompt(prompt, MAX_USER_PROMPT_CHARS)

        payload = {
            "model": target_model,
            "prompt": prompt_safe,
            "system": system_safe,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,     # Fully deterministic
                "num_predict": max_output_tokens,  # Hard token limit
                "num_ctx": 2048,        # Context window (fits in 4GB VRAM)
                "top_k": 10,            # Tight sampling for consistent JSON
                "top_p": 0.9,
            },
        }

        raw_response = "{}"
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "{}")
            json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw_response)
            clean_json = json_match.group(1) if json_match else raw_response
            result = json.loads(clean_json)
            log.info("llm_compact_json_success", tokens_used=data.get("eval_count", "?"))
            return result
        except json.JSONDecodeError:
            log.warning("llm_compact_json_parse_failed", raw=raw_response[:300])
            # Retry with even shorter prompt
            return await self._retry_json_minimal(prompt_safe, target_model, max_output_tokens)
        except Exception as e:
            log.error("llm_compact_json_failed", error=str(e))
            raise e

    async def _retry_json_minimal(
        self,
        original_prompt: str,
        model: str,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Emergency retry with minimal prompt if first attempt failed to parse."""
        # Extract just the first 200 chars of the original prompt
        minimal_prompt = original_prompt[:200]
        payload = {
            "model": model,
            "prompt": minimal_prompt,
            "system": "Return ONLY valid JSON. No explanations. No markdown.",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": max_tokens,
                "num_ctx": 1024,
            },
        }
        raw_response = "{}"
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "{}")
            json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw_response)
            clean_json = json_match.group(1) if json_match else raw_response
            return json.loads(clean_json)
        except Exception as e:
            log.error("llm_retry_failed", error=str(e), raw=raw_response[:100])
            return {}

    # ------------------------------------------------------------------
    # NEW: Narrator — for 1-2 sentence clinical explanations only
    # ------------------------------------------------------------------

    async def generate_narrator(
        self,
        short_prompt: str,
        model: str | None = None,
    ) -> str:
        """
        Ultra-short text generation for clinical narrative (1-2 sentences).
        Used when the LLM only needs to write explanations for pre-ranked candidates.
        Max 200 output tokens. Temperature 0.
        """
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": short_prompt[:600],
            "system": "You are a senior physician. Write 1-2 concise clinical sentences. Be specific. No preamble.",
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": MAX_TOKENS_NARRATIVE,
                "num_ctx": 1024,
            },
        }
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            log.error("ollama_narrator_failed", error=str(e))
            return ""

    # ------------------------------------------------------------------
    # Model info
    # ------------------------------------------------------------------

    async def list_models(self):
        """List available Ollama models."""
        try:
            r = await self.client.get("/api/tags")
            return r.json().get("models", [])
        except Exception:
            return []

    async def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        models = await self.list_models()
        return any(m.get("name", "").startswith(model_name) for m in models)


llm_service = OllamaService()
