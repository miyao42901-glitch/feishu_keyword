"""共享 Redis 连接（限流、异步任务缓存与调度）。"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

import redis

from config.settings import get_settings

_client: Optional[redis.Redis] = None


@lru_cache
def redis_url() -> str:
    return get_settings().redis_url.strip()


def redis_configured() -> bool:
    return bool(redis_url())


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        url = redis_url()
        if not url:
            raise RuntimeError("REDIS_URL is empty")
        _client = redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=5,
        )
    return _client


def ping_redis() -> bool:
    if not redis_configured():
        return False
    try:
        return bool(get_redis().ping())
    except redis.RedisError:
        return False
