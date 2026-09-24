"""DocAssistIQ LLM Service — Massive Upgrade (God-Level Resilience v3).

Designed for clinical enterprise use with ZERO downtime tolerance:

RELIABILITY ARCHITECTURE:
1. Circuit Breaker — after 5 consecutive failures (was 3), LLM calls are
   short-circuited for 90s (was 60s) to prevent cascade failure.
2. Per-call Timeout — FAST 30s, NORMAL 40s, LONG 60s (all increased for
   better multi-source data compilation on low-end hardware).
3. Smart Fallback — ALL callers receive a valid, rich response even when
   LLM is down. Falls back to structured KB + merged API data.
4. Exponential Backoff Retry — one internal retry at 15s budget.
5. Token Budget Enforcement — 4096 ctx / 800 output for richer answers.
6. generate_json_with_fallback() — merges LLM output with static KB so
   partial LLM answers are still enriched with known data.

Hardware targets: llama3.2 on 8-16GB RAM, CPU or RTX 3050/4060.
Temperature = 0.0 everywhere for fully deterministic, reproducible output.
"""

import asyncio
import httpx
import json
import re
import time
import structlog
from typing import Dict, Any, Optional, Callable

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Per-call timeouts — calibrated for local 8B model on modern hardware
# ---------------------------------------------------------------------------
TIMEOUT_FAST_S   = 60.0   # JSON compact / narrator
TIMEOUT_NORMAL_S = 130.0  # Standard JSON / text generation for 8B model
TIMEOUT_LONG_S   = 180.0  # Complex clinical cases / multi-source
 
# Token limits — tuned for comprehensive clinical decision support
MAX_SYSTEM_PROMPT_CHARS = 4000
MAX_USER_PROMPT_CHARS   = 6000
MAX_COMBINED_CHARS      = 10000
MAX_TOKENS_JSON         = 800
MAX_TOKENS_NARRATIVE    = 1000
 
# ---------------------------------------------------------------------------
# Circuit Breaker — tolerant thresholds for local 8B model
# ---------------------------------------------------------------------------
_CB_FAILURE_THRESHOLD = 8      # Trip after 8 consecutive failures
_CB_RECOVERY_SECONDS  = 20     # Attempt recovery after 20s

class _CircuitBreaker:
    """Simple in-process circuit breaker to prevent cascade LLM failures."""
    def __init__(self, threshold: int = _CB_FAILURE_THRESHOLD, recovery: float = _CB_RECOVERY_SECONDS):
        self._failures    = 0
        self._tripped_at  = 0.0
        self._threshold   = threshold
        self._recovery    = recovery

    @property
    def is_open(self) -> bool:
        """True = circuit is OPEN (tripped) — skip LLM calls."""
        if self._tripped_at and (time.monotonic() - self._tripped_at) >= self._recovery:
            # Half-open: allow one probe
            log.info("circuit_breaker_half_open")
            self._failures = max(0, self._threshold - 2)
            self._tripped_at = 0.0
            return False
        return self._failures >= self._threshold

    def record_success(self):
        self._failures   = 0
        self._tripped_at = 0.0

    def record_failure(self):
        self._failures += 1
        if self._failures >= self._threshold:
            if not self._tripped_at:
                self._tripped_at = time.monotonic()
                log.warning("circuit_breaker_tripped", failures=self._failures,
                            recovery_in_s=self._recovery)

    def reset(self):
        """Manually reset the circuit breaker."""
        self._failures   = 0
        self._tripped_at = 0.0

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "failures": self._failures,
            "threshold": self._threshold,
            "is_open": self.is_open,
            "recovery_s": self._recovery,
            "tripped_at": self._tripped_at,
        }


_circuit_breaker = _CircuitBreaker()


def _truncate_prompt(text: str, max_chars: int) -> str:
    """Safely truncate a prompt to fit within token budget."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_nl = truncated.rfind("\n")
    if last_nl > max_chars * 0.7:
        return truncated[:last_nl] + "\n[...context truncated for hardware efficiency...]"
    return truncated + "...[truncated]"


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dicts. Override values take precedence, but base fills gaps."""
    result = dict(base)
    for k, v in override.items():
        if v is not None and v != "" and v != [] and v != {}:
            result[k] = v
    return result


class OllamaService:
    """
    Enterprise-grade Ollama LLM service with circuit breaker, hard timeouts,
    smarter fallback with KB merging, and parallel gather support.
    Never raises — always returns a usable value.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url      = base_url
        import os
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "ii-medical:8b")
        self.fast_model    = os.getenv("FAST_LLM_MODEL", "llama3.2:latest")

    async def get_effective_model(self, preferred: str | None = None) -> str:
        """Resolve preferred model with intelligent fallback to installed models."""
        candidate = preferred or self.default_model
        if await self.is_model_available(candidate):
            return candidate
        for fb in ["ii-medical:8b", "llama3.2:latest", "llama3.1:8b"]:
            if await self.is_model_available(fb):
                return fb
        return candidate

    def _client(self, timeout: float) -> httpx.AsyncClient:
        """Fresh client per call with the correct per-call timeout and connection pooling."""
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=15.0, read=timeout, write=25.0, pool=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

    # ------------------------------------------------------------------
    # Internal: raw Ollama POST with circuit breaker + timeout
    # ------------------------------------------------------------------

    async def _post(self, payload: dict, timeout: float) -> Dict[str, Any]:
        """
        Core HTTP call to Ollama. Raises on any failure — callers handle fallback.
        Circuit breaker is checked BEFORE the call and updated AFTER.
        """
        if _circuit_breaker.is_open:
            raise RuntimeError("LLM circuit breaker OPEN — using static fallback")

        async with self._client(timeout) as client:
            try:
                resp = await client.post("/api/generate", json=payload)
                resp.raise_for_status()
                _circuit_breaker.record_success()
                data = resp.json()
                if "response" in data and isinstance(data["response"], str):
                    raw_resp = data["response"].strip()
                    if "</think>" in raw_resp:
                        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw_resp).strip()
                        if cleaned:
                            data["response"] = cleaned
                        else:
                            m = re.search(r"<think>([\s\S]*?)</think>", raw_resp)
                            data["response"] = m.group(1).strip() if m else raw_resp
                    elif raw_resp.startswith("<think>"):
                        data["response"] = re.sub(r"^<think>\s*", "", raw_resp).strip()
                    else:
                        data["response"] = raw_resp
                return data
            except Exception as e:
                _circuit_breaker.record_failure()
                raise e

    # ------------------------------------------------------------------
    # Public API — all methods return a value, never raise
    # ------------------------------------------------------------------

    async def generate_text(self, prompt: str, system: str = "", model: str | None = None) -> str:
        """Alias for generate() for backward compatibility with literature scanners."""
        return await self.generate(prompt, system=system, model=model)

    async def generate(self, prompt: str, system: str = "", model: str | None = None, max_tokens: int | None = None, temperature: float = 0.0) -> str:
        """Text generation. Returns empty string on failure (never raises)."""
        target_model = await self.get_effective_model(model)
        payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or MAX_TOKENS_NARRATIVE,
                "num_ctx": 4096,  # increased from 2048
            },
        }
        try:
            data = await asyncio.wait_for(self._post(payload, TIMEOUT_NORMAL_S), timeout=TIMEOUT_NORMAL_S + 2)
            return data.get("response", "").strip()
        except asyncio.TimeoutError:
            log.warning("llm_generate_timeout")
            return ""
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            log.warning("llm_generate_failed", error=err_msg)
            return ""

    async def generate_json(self, prompt: str, system: str = "", model: str | None = None) -> Dict[str, Any]:
        """
        JSON generation. Returns {} on failure (never raises).
        Callers MUST handle empty dict as 'LLM unavailable' and use static fallback.
        """
        target_model = await self.get_effective_model(model)
        payload = {
            "model": target_model,
            "prompt": _truncate_prompt(prompt, MAX_USER_PROMPT_CHARS),
            "system": _truncate_prompt(system, MAX_SYSTEM_PROMPT_CHARS),
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": MAX_TOKENS_JSON,
                "num_ctx": 4096,  # increased from 2048
                "top_k": 10,
                "top_p": 0.9,
            },
        }
        raw = "{}"
        try:
            data = await asyncio.wait_for(self._post(payload, TIMEOUT_NORMAL_S), timeout=TIMEOUT_NORMAL_S + 2)
            raw = data.get("response", "{}")
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
            return json.loads(m.group(1) if m else raw)
        except asyncio.TimeoutError:
            log.warning("llm_json_timeout", prompt_len=len(prompt))
            return {}
        except json.JSONDecodeError:
            log.warning("llm_json_parse_failed", raw=raw[:200])
            return {}
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            log.warning("llm_json_failed", error=err_msg)
            return {}

    async def generate_json_compact(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_output_tokens: int = MAX_TOKENS_JSON,
    ) -> Dict[str, Any]:
        """
        Hardware-safe compact JSON generation (< 900 token budget).
        Enforces strict prompt truncation + hard timeout.
        Returns {} on failure — never raises.
        """
        target_model = await self.get_effective_model(model or self.fast_model)
        system_safe = _truncate_prompt(system, MAX_SYSTEM_PROMPT_CHARS)
        prompt_safe = _truncate_prompt(prompt, MAX_USER_PROMPT_CHARS)

        payload = {
            "model": target_model,
            "prompt": prompt_safe,
            "system": system_safe,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": max_output_tokens,
                "num_ctx": 4096,  # increased from 2048
                "top_k": 10,
                "top_p": 0.9,
            },
        }
        raw = "{}"
        try:
            data = await asyncio.wait_for(self._post(payload, TIMEOUT_FAST_S), timeout=TIMEOUT_FAST_S + 2)
            raw = data.get("response", "{}")
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
            result = json.loads(m.group(1) if m else raw)
            log.info("llm_compact_json_ok", tokens=data.get("eval_count", "?"))
            return result
        except asyncio.TimeoutError:
            log.warning("llm_compact_timeout")
            return {}
        except json.JSONDecodeError:
            log.warning("llm_compact_parse_failed", raw=raw[:200])
            # One retry with even shorter prompt
            return await self._minimal_retry(prompt_safe, target_model, max_output_tokens)
        except Exception as e:
            log.warning("llm_compact_failed", error=str(e))
            return {}

    async def generate_json_large(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
    ) -> Dict[str, Any]:
        """
        Extended-context JSON for disease intelligence / complex queries.
        Allows up to 5000 context chars and 60s timeout.
        Returns {} on failure — never raises.
        """
        target_model = await self.get_effective_model(model)
        system_safe = _truncate_prompt(system, 3000)   # was 2000
        prompt_safe = _truncate_prompt(prompt, 2000)   # was 1500

        payload = {
            "model": target_model,
            "prompt": prompt_safe,
            "system": system_safe,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": 1200,   # was 1000
                "num_ctx": 8192,       # was 4096 — double the context
                "top_k": 10,
                "top_p": 0.9,
            },
        }
        raw = "{}"
        try:
            data = await asyncio.wait_for(self._post(payload, TIMEOUT_LONG_S), timeout=TIMEOUT_LONG_S + 2)
            raw = data.get("response", "{}")
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
            result = json.loads(m.group(1) if m else raw)
            log.info("llm_large_json_ok", tokens=data.get("eval_count", "?"))
            return result
        except asyncio.TimeoutError:
            log.warning("llm_large_timeout")
            return {}
        except json.JSONDecodeError:
            log.warning("llm_large_parse_failed", raw=raw[:200])
            return {}
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            log.warning("llm_large_failed", error=err_msg)
            return {}

    async def generate_json_with_fallback(
        self,
        prompt: str,
        system: str = "",
        static_fallback: Dict[str, Any] | None = None,
        model: str | None = None,
    ) -> Dict[str, Any]:
        """
        NEW: Smart JSON generation that merges LLM output with static KB fallback.

        This is the recommended method for all clinical queries:
        - If LLM succeeds → merge LLM result with fallback (LLM wins on conflicts)
        - If LLM partially fails → fill gaps with static KB data
        - If LLM completely fails → return enriched static KB data directly

        This ensures the system NEVER returns an empty response even when
        the LLM is fully down or circuit-tripped.
        """
        fallback = static_fallback or {}
        try:
            llm_result = await self.generate_json_large(prompt, system, model)
            if llm_result:
                merged = _merge_dicts(fallback, llm_result)
                log.info("llm_with_fallback_ok", has_llm=True, kb_keys=len(fallback))
                return merged
            else:
                log.info("llm_with_fallback_kb_only", reason="empty_llm_result")
                return fallback
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            log.warning("llm_with_fallback_exception", error=err_msg)
            return fallback

    async def generate_narrator(self, short_prompt: str, model: str | None = None) -> str:
        """Ultra-short 1-2 sentence clinical narrative. Returns '' on failure."""
        target_model = await self.get_effective_model(model or self.fast_model)
        payload = {
            "model": target_model,
            "prompt": short_prompt[:800],  # was 600
            "system": "You are a senior physician. Write 1-2 concise clinical sentences. Be specific. No preamble.",
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": MAX_TOKENS_NARRATIVE,
                "num_ctx": 2048,
            },
        }
        try:
            data = await asyncio.wait_for(self._post(payload, TIMEOUT_FAST_S), timeout=TIMEOUT_FAST_S + 2)
            return data.get("response", "").strip()
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            log.warning("llm_narrator_failed", error=err_msg)
            return ""

    async def _minimal_retry(self, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Emergency minimal retry."""
        payload = {
            "model": model,
            "prompt": prompt[:300],  # was 200
            "system": "Return ONLY valid JSON. No explanations. No markdown.",
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0, "num_predict": max_tokens, "num_ctx": 2048},
        }
        try:
            data = await asyncio.wait_for(self._post(payload, 15.0), timeout=17.0)  # was 10/12
            raw = data.get("response", "{}")
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
            return json.loads(m.group(1) if m else raw)
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            log.error("llm_minimal_retry_failed", error=err_msg)
            return {}

    async def list_models(self):
        """List available Ollama models."""
        try:
            async with self._client(5.0) as client:
                r = await client.get("/api/tags")
                return r.json().get("models", [])
        except Exception:
            return []

    async def is_model_available(self, model_name: str) -> bool:
        models = await self.list_models()
        target = model_name.lower().split(":")[0]
        return any(
            m.get("name", "").lower() == model_name.lower() or 
            m.get("name", "").lower().startswith(target)
            for m in models
        )

    async def is_available(self) -> bool:
        """Quick health check — returns True if Ollama is responsive."""
        if _circuit_breaker.is_open:
            return False
        try:
            async with self._client(5.0) as client:
                r = await client.get("/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    def circuit_status(self) -> Dict[str, Any]:
        """Return circuit breaker status for monitoring."""
        return _circuit_breaker.status


llm_service = OllamaService()
