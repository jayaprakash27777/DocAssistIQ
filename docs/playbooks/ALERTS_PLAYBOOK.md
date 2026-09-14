# DocAssistIQ Alert Operator Playbook (Phase 67)

This playbook defines actionable thresholds, severity, triggers, and the explicit operator response for infrastructure and AI observability alerts.

## Core Infrastructure

### `DatabaseDown`
- **Severity**: CRITICAL
- **Trigger**: `pg_up == 0` for 2m
- **Cooldown**: 10m
- **Operational Context**: The primary PostgreSQL instance is unreachable, halting all DB operations.
- **Operator Response**:
  1. Verify the status of the PostgreSQL container/service (`systemctl status postgresql` or `docker ps`).
  2. Check disk space (`df -h`). If full, clear WAL logs or expand volume.
  3. Failover to read-replica if the primary is unrecoverable.

### `RedisDown`
- **Severity**: CRITICAL
- **Trigger**: `redis_up == 0` for 2m
- **Cooldown**: 5m
- **Operational Context**: Redis is used for API rate limiting, caching, and Celery task queues.
- **Operator Response**:
  1. Check Redis memory limits (`INFO memory`). If OOM, restart Redis and adjust `maxmemory`.
  2. Ensure the network route to the Redis cluster is healthy.

### `APIHighErrorRate`
- **Severity**: CRITICAL
- **Trigger**: `HTTP 5xx > 5%` over 5 minutes.
- **Cooldown**: 15m
- **Operational Context**: Users are experiencing widespread internal server errors.
- **Operator Response**:
  1. Check `fastapi` application logs for unhandled exception stack traces.
  2. Check if a downstream dependency (DB/Redis/AI Provider) is failing but not triggering its own alert.
  3. If related to a new deployment, initiate a rollback.

---

## AI Observability

### `AILatencyBreach`
- **Severity**: WARNING
- **Trigger**: `90th percentile latency > 2.5s` over 5m.
- **Cooldown**: 30m
- **Operational Context**: The AI pipeline (Inference, ASR, or RAG) is slow, degrading the real-time clinical experience.
- **Operator Response**:
  1. Identify the specific bottleneck via the `operation` label (e.g., `asr_transcription`).
  2. Check if GPU VRAM is full or if the provider is throttling us (e.g., rate limits).
  3. If it's a provider issue, toggle the fallback provider in the ML Registry.

### `AIModelErrorSpike`
- **Severity**: CRITICAL
- **Trigger**: `rate(ai_model_errors_total) > 1/sec` for 3m.
- **Cooldown**: 15m
- **Operational Context**: The AI model is throwing exceptions (e.g., context window exceeded, malformed JSON output, API timeout).
- **Operator Response**:
  1. Check the `error_type` label.
  2. If `TimeoutError`, increase the timeout threshold or failover to a faster adapter.
  3. If `JSONDecodeError`, the model is hallucinating output structures. Revert to a previous `APPROVED` model version using the ML Registry Service.

### `RAGRetrievalFailure`
- **Severity**: CRITICAL
- **Trigger**: `rate(ai_model_errors_total{operation="rag_retrieval"}) > 0.5/sec` for 3m.
- **Cooldown**: 15m
- **Operational Context**: Vector DB is failing to return context, meaning the model is operating "Zero-Shot", risking hallucination.
- **Operator Response**:
  1. Verify the `pgvector` index is intact.
  2. Check if the embedding model server is down.

---

## Background Workers

### `CeleryWorkerDown`
- **Severity**: WARNING
- **Trigger**: Celery worker heartbeat missing for 3m.
- **Cooldown**: 15m
- **Operational Context**: Background knowledge ingestion or asynchronous tasks are stalled.
- **Operator Response**:
  1. Restart the Celery worker deployment.
  2. Check if a specific poison-pill task is causing OOM crashes.

### `WebSocketDropSpike`
- **Severity**: WARNING
- **Trigger**: High rate of client WS disconnects.
- **Cooldown**: 10m
- **Operational Context**: Real-time consultation streaming is degraded.
- **Operator Response**:
  1. Check the load balancer config (timeout settings).
  2. Verify if the FastAPI server is CPU-starved and dropping connections.
