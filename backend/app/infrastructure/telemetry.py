"""DocAssistIQ ?" AI Observability Telemetry (Phase 66).

Real-time, industry-grade AI observability using Prometheus.
"""

import time
import functools
import logging
from typing import Callable, Any
from prometheus_client import Histogram, Counter

# Ensure logging doesn't log patient text (only structural data).
logger = logging.getLogger("docassistiq.ai.telemetry")

# ==============================================================================
# PROMETHEUS METRICS DEFINITIONS
# ==============================================================================

# 1. Latency Histograms
AI_LATENCY = Histogram(
    "ai_operation_latency_seconds",
    "Latency of AI operations (inference, asr, embedding, retrieval)",
    ["operation", "provider_name", "status"]
)

# 2. Counters
AI_ERRORS = Counter(
    "ai_model_errors_total",
    "Total number of AI model errors",
    ["operation", "provider_name", "error_type"]
)

AI_TIMEOUTS = Counter(
    "ai_timeout_total",
    "Total number of AI operation timeouts",
    ["operation", "provider_name"]
)

AI_SAFETY_FLAGS = Counter(
    "ai_safety_flags_total",
    "Total number of clinical safety violations intercepted",
    ["operation", "provider_name", "flag_type"]
)

AI_ABSTENTIONS = Counter(
    "ai_abstention_total",
    "Total number of times the AI voluntarily abstained from diagnosis",
    ["operation", "provider_name"]
)


# ==============================================================================
# OBSERVABILITY DECORATOR
# ==============================================================================

def observe_ai(operation: str, provider_name: str = "default_provider"):
    """
    Decorator to automatically instrument an AI function with Prometheus metrics.
    Tracks latency, detects errors/timeouts, and records correlation data.
    
    WARNING: Do not log positional args (args, kwargs) to avoid HIPAA leaks.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # We explicitly check for a 'correlation_id' kwarg for tracing
            correlation_id = kwargs.get("correlation_id", "unknown_trace")
            
            logger.info(
                f"[AI_TRACE: {correlation_id}] Starting AI Operation '{operation}' "
                f"using provider '{provider_name}'"
            )
            
            start_time = time.perf_counter()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                
                # Check if it was an intentional abstention
                # Assuming our pipeline returns an object with a condition_code
                if hasattr(result, "condition_code") and getattr(result, "condition_code") == "ABSTAIN":
                    AI_ABSTENTIONS.labels(operation=operation, provider_name=provider_name).inc()
                    status = "abstain"
                    logger.warning(f"[AI_TRACE: {correlation_id}] AI Abstained from prediction.")
                    
                return result

            except TimeoutError as e:
                status = "timeout"
                AI_TIMEOUTS.labels(operation=operation, provider_name=provider_name).inc()
                logger.error(f"[AI_TRACE: {correlation_id}] AI Timeout in '{operation}'")
                raise e

            except Exception as e:
                status = "error"
                # Exclude potentially sensitive exception message data, log only type
                error_type = type(e).__name__
                AI_ERRORS.labels(
                    operation=operation, 
                    provider_name=provider_name, 
                    error_type=error_type
                ).inc()
                logger.error(f"[AI_TRACE: {correlation_id}] AI Error ({error_type}) in '{operation}'")
                raise e
            
            finally:
                latency = time.perf_counter() - start_time
                AI_LATENCY.labels(
                    operation=operation, 
                    provider_name=provider_name, 
                    status=status
                ).observe(latency)
                
                logger.info(
                    f"[AI_TRACE: {correlation_id}] Completed '{operation}' "
                    f"in {latency:.4f}s with status '{status}'"
                )

        return sync_wrapper
    return decorator
