"""DocAssistIQ Backend — Redis infrastructure.

Provides a connection pool and a probe function for the readiness check.
Uses the synchronous redis client for simplicity in the readiness probe.
The async client will be used in later phases for pub/sub and caching.
"""

import redis
import redis.asyncio as aioredis

from app.config import get_settings

_async_client: aioredis.Redis | None = None


def get_sync_client() -> redis.Redis:
    """Return a new synchronous Redis client (for probing)."""
    settings = get_settings()
    return redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )


def get_async_client() -> aioredis.Redis:
    """Return (or lazily create) the shared async Redis client."""
    global _async_client  # noqa: PLW0603
    if _async_client is None:
        settings = get_settings()
        _async_client = aioredis.Redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            socket_connect_timeout=3,
            socket_timeout=3,
            decode_responses=True,
        )
    return _async_client


def probe_redis() -> None:
    """Probe Redis connectivity synchronously. Raises on failure.

    Uses PING with a short timeout.
    Called by the /ready endpoint.
    """
    client = get_sync_client()
    try:
        client.ping()
    finally:
        client.close()


async def close_async_client() -> None:
    """Close the async Redis client (call on application shutdown)."""
    global _async_client  # noqa: PLW0603
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
