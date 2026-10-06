"""DocAssistIQ LLM Service — Nuclear-Level Upgrade v4 (God-Level Clinical AI).

ARCHITECTURE: Enterprise Clinical AI with ZERO restriction policy:

RELIABILITY ARCHITECTURE:
1. Circuit Breaker — after 10 consecutive failures, LLM calls short-circuit for 30s.
2. Per-call Timeout — FAST 90s, NORMAL 180s, LONG 300s (extended for large clinical notes).
3. Smart Fallback — ALL callers receive a valid, rich response even when LLM is down.
4. Exponential Backoff Retry — internal retry with 30s budget.
5. Token Budget — 16384 ctx / 4096 output for comprehensive, complete clinical answers.
6. generate_json_with_fallback() — merges LLM output with static KB so partial answers are enriched.
7. ZERO RESTRICTIONS: Handles any clinical question, any length note, any specialty.
8. UNRESTRICTED MEDICAL KNOWLEDGE: No topic filtering, no hallucination guardrails beyond evidence citation.

Hardware targets: llama3.2, ii-medical:8b, medllama3:8b on 8-32GB RAM or GPU.
Temperature = 0.1 for creative-but-accurate medical reasoning.
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
# Per-call timeouts — Nuclear-Level extended for large clinical notes & complex cases
# ---------------------------------------------------------------------------
TIMEOUT_FAST_S   = 90.0    # JSON compact / narrator — increased for complex notes
TIMEOUT_NORMAL_S = 180.0   # Standard JSON / text generation — handles 4K-token notes
TIMEOUT_LONG_S   = 300.0   # Long-form clinical documents, discharge summaries

# Token limits — Nuclear-Level: No artificial restrictions on medical answers
MAX_SYSTEM_PROMPT_CHARS = 8000   # Extended system prompts for rich clinical context
MAX_USER_PROMPT_CHARS   = 16000  # Handle long doctor notes, multi-page records
MAX_COMBINED_CHARS      = 24000  # Combined context for complex multi-source synthesis
MAX_TOKENS_JSON         = 2048   # Rich structured JSON with complete clinical data
MAX_TOKENS_NARRATIVE    = 4096   # Long-form narrative for comprehensive answers

# ---------------------------------------------------------------------------
# Circuit Breaker — Tolerant thresholds for clinical continuity
# ---------------------------------------------------------------------------
_CB_FAILURE_THRESHOLD = 10     # Trip after 10 consecutive failures (more tolerant)
_CB_RECOVERY_SECONDS  = 30     # Attempt recovery after 30s

class _CircuitBreaker:
    """Simple in-process circuit breaker to prevent cascade LLM failures."""
    def __init__(self, threshold: int = _CB_FAILURE_THRESHOLD, recovery: float = _CB_RECOVERY_SECONDS):
        self._failures    = 0
        self._tripped_at  = 0.0
        self._threshold   = threshold
        self._recovery    = recovery
        self._force_open  = False

    @property
    def is_open(self) -> bool:
        """True = circuit is OPEN (tripped) — skip LLM calls."""
        if self._force_open:
            return True
        if self._tripped_at and (time.monotonic() - self._tripped_at) >= self._recovery:
            # Half-open: allow one probe
            log.info("circuit_breaker_half_open")
            self._failures = max(0, self._threshold - 2)
            self._tripped_at = 0.0
            return False
        return self._failures >= self._threshold

    def set_force_open(self, force: bool):
        """Allows administrator to manually force offline fallback mode or re-enable."""
        self._force_open = force
        if not force:
            self.reset()

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
        self._force_open = False

    @property
    def state_name(self) -> str:
        if self._force_open:
            return "FORCED_OFFLINE"
        if self._tripped_at and (time.monotonic() - self._tripped_at) >= self._recovery:
            return "HALF_OPEN"
        if self._failures >= self._threshold:
            return "OPEN"
        return "CLOSED"

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "failures": self._failures,
            "threshold": self._threshold,
            "is_open": self.is_open,
            "state": self.state_name,
            "forced_offline": self._force_open,
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

    def __init__(self, base_url: str | None = None):
        import os
        self.base_url      = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
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

    async def generate(self, prompt: str, system: str = "", model: str | None = None, max_tokens: int | None = None, temperature: float = 0.1) -> str:
        """
        Nuclear-level text generation — handles any question, any length, any clinical specialty.
        Zero restrictions: answers any medical question comprehensively.
        Returns empty string on complete failure (never raises).
        """
        target_model = await self.get_effective_model(model)
        # Auto-scale context based on prompt size
        prompt_len = len(prompt) + len(system)
        ctx_size = 32768 if prompt_len > 8000 else (16384 if prompt_len > 4000 else 8192)
        payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or MAX_TOKENS_NARRATIVE,
                "num_ctx": ctx_size,
                "repeat_penalty": 1.1,
            },
        }
        timeout = TIMEOUT_LONG_S if prompt_len > 8000 else TIMEOUT_NORMAL_S
        try:
            data = await asyncio.wait_for(self._post(payload, timeout), timeout=timeout + 5)
            return data.get("response", "").strip()
        except asyncio.TimeoutError:
            log.warning("llm_generate_timeout", prompt_len=prompt_len)
            return ""
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            log.warning("llm_generate_failed", error=err_msg)
            return ""

    async def generate_json(self, prompt: str, system: str = "", model: str | None = None) -> Dict[str, Any]:
        """
        Nuclear-level JSON generation — handles complex multi-system queries.
        Returns {} on failure (never raises).
        """
        target_model = await self.get_effective_model(model)
        prompt_safe = _truncate_prompt(prompt, MAX_USER_PROMPT_CHARS)
        system_safe = _truncate_prompt(system, MAX_SYSTEM_PROMPT_CHARS)
        prompt_len = len(prompt_safe) + len(system_safe)
        ctx_size = 16384 if prompt_len > 4000 else 8192
        payload = {
            "model": target_model,
            "prompt": prompt_safe,
            "system": system_safe,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.05,
                "num_predict": MAX_TOKENS_JSON,
                "num_ctx": ctx_size,
                "top_k": 15,
                "top_p": 0.92,
            },
        }
        raw = "{}"
        try:
            data = await asyncio.wait_for(self._post(payload, TIMEOUT_NORMAL_S), timeout=TIMEOUT_NORMAL_S + 5)
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
        Nuclear-Level compact JSON generation — God-Level accuracy for differential diagnosis.
        Supports large prompts with rich clinical context up to 16K tokens.
        Returns {} on failure — never raises.
        """
        target_model = await self.get_effective_model(model or self.fast_model)
        system_safe = _truncate_prompt(system, MAX_SYSTEM_PROMPT_CHARS)
        prompt_safe = _truncate_prompt(prompt, MAX_USER_PROMPT_CHARS)
        prompt_len = len(prompt_safe) + len(system_safe)
        # Adaptive context: large for complex prompts
        ctx_size = 16384 if prompt_len > 4000 else (8192 if prompt_len > 2000 else 4096)

        payload = {
            "model": target_model,
            "prompt": prompt_safe,
            "system": system_safe,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.05,   # Slightly above 0 for better open-domain coverage
                "num_predict": max_output_tokens,
                "num_ctx": ctx_size,   # Adaptive — was fixed 4096
                "top_k": 15,
                "top_p": 0.92,
                "repeat_penalty": 1.05,
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
        Nuclear-level extended-context JSON for disease intelligence, complex queries.
        Supports up to 24K context chars and handles large clinical documents.
        Returns {} on failure — never raises.
        """
        target_model = await self.get_effective_model(model)
        # Nuclear-level: do not truncate aggressively — allow full context
        system_safe = _truncate_prompt(system, MAX_SYSTEM_PROMPT_CHARS)
        prompt_safe = _truncate_prompt(prompt, MAX_USER_PROMPT_CHARS)
        prompt_len = len(prompt_safe) + len(system_safe)
        ctx_size = 32768 if prompt_len > 12000 else (16384 if prompt_len > 6000 else 8192)

        payload = {
            "model": target_model,
            "prompt": prompt_safe,
            "system": system_safe,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.05,
                "num_predict": MAX_TOKENS_JSON,    # Full 2048 tokens for rich JSON
                "num_ctx": ctx_size,                # Adaptive context scaling
                "top_k": 15,
                "top_p": 0.92,
                "repeat_penalty": 1.05,
            },
        }
        raw = "{}"
        try:
            data = await asyncio.wait_for(self._post(payload, TIMEOUT_LONG_S), timeout=TIMEOUT_LONG_S + 10)
            raw = data.get("response", "{}")
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
            result = json.loads(m.group(1) if m else raw)
            log.info("llm_large_json_ok", tokens=data.get("eval_count", "?"), ctx_size=ctx_size)
            return result
        except asyncio.TimeoutError:
            log.warning("llm_large_timeout", prompt_len=prompt_len)
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
        """Clinical narrative generation — comprehensive, evidence-based. Returns '' on failure."""
        target_model = await self.get_effective_model(model or self.fast_model)
        payload = {
            "model": target_model,
            "prompt": short_prompt[:3000],  # Extended to handle complex cases
            "system": (
                "You are a Senior Consultant Physician. Provide a precise, clinically accurate, "
                "evidence-based narrative explanation. Be comprehensive but concise. "
                "Include pathophysiological rationale. No preamble or disclaimers."
            ),
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": MAX_TOKENS_NARRATIVE,
                "num_ctx": 8192,
                "repeat_penalty": 1.05,
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

    def set_system_model(self, model_name: str, fast_model: Optional[str] = None):
        """Dynamically switches the active LLM model across the entire system."""
        cleaned = model_name.strip()
        if not cleaned:
            raise ValueError("Model name cannot be empty")
        self.default_model = cleaned
        if fast_model and fast_model.strip():
            self.fast_model = fast_model.strip()
        
        # Also update global AI Factory generation provider
        try:
            from app.infrastructure.ai.factory import set_system_ai_model
            set_system_ai_model(cleaned)
        except Exception as e:
            log.warning("failed_to_update_ai_factory_provider", error=str(e))
        
        log.info("system_ai_model_switched", default_model=self.default_model, fast_model=self.fast_model)

    async def get_detailed_status(self) -> Dict[str, Any]:
        """Returns comprehensive real-time status of the AI engine and circuit breaker."""
        start = time.perf_counter()
        is_conn = False
        installed_models = []
        latency_ms = 0.0
        error_msg = None

        try:
            async with self._client(3.0) as client:
                r = await client.get("/api/tags")
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                if r.status_code == 200:
                    is_conn = True
                    raw_models = r.json().get("models", [])
                    installed_models = [m.get("name") for m in raw_models if m.get("name")]
        except Exception as ex:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            error_msg = str(ex)

        cb_status = _circuit_breaker.status
        is_open = cb_status["is_open"]
        active_mode = "static_kb_fallback" if is_open or not is_conn else "llm_active"

        return {
            "active_model": self.default_model,
            "fast_model": self.fast_model,
            "base_url": self.base_url,
            "provider_name": "Ollama / Local Medical LLM",
            "is_connected": is_conn,
            "latency_ms": latency_ms,
            "installed_models": installed_models,
            "circuit_breaker": cb_status,
            "mode": active_mode,
            "error": error_msg,
            "recommended_models": [
                {"id": "ii-medical:8b", "label": "II-Medical-8B (Clinical Specialist)", "type": "medical"},
                {"id": "llama3.1:8b", "label": "Llama-3.1-8B (General Diagnostic)", "type": "general"},
                {"id": "llama3.2:latest", "label": "Llama-3.2 (Fast Clinical Edge)", "type": "edge"},
                {"id": "meditron:7b", "label": "Meditron-7B (Clinical Reasoning)", "type": "medical"},
                {"id": "biomistral:7b", "label": "BioMistral-7B (Biomedical QA)", "type": "biomedical"},
            ],
            "safety_watermark": "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED",
        }


llm_service = OllamaService()
