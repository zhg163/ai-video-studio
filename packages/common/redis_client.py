"""Redis async client."""

from __future__ import annotations

import redis.asyncio as aioredis

from packages.common.config import settings

_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Get or create the global Redis client."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
