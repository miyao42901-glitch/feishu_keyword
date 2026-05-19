"""按客户端 IP 的滑动窗口限流（Redis ZSET；Redis 不可用时回退进程内计数）。"""

from __future__ import annotations

import logging
import random
import re
import time
from collections import deque
from threading import Lock
from typing import Deque

from fastapi import Depends, Request

from social_platform.api_response import ApiHttpError
from social_platform.api_status_codes import CODE_RATE_LIMIT_EXCEEDED, get_message
from social_platform.redis_client import get_redis, redis_configured

logger = logging.getLogger(__name__)

_buckets: dict[tuple[str, str], Deque[float]] = {}
_lock = Lock()

RATE_LIMIT_KEY_PREFIX = "feishu:ratelimit:"
_SCOPE_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def normalize_rate_limit_scope(scope: str) -> str:
    """
    限流桶名：仅允许短标识（字母开头），禁止 URL/path，避免 Redis key 爆炸。
    """
    s = (scope or "").strip().lower()
    if not s or not _SCOPE_RE.fullmatch(s):
        raise ValueError(
            "rate limit scope must be a short name like async_submit, not a URL path"
        )
    return s


def _redis_rate_limit_key(ip: str, scope: str) -> str:
    """feishu:ratelimit:{scope}:{ip} — 不含 method/path/URL。"""
    safe_ip = (ip or "unknown").replace(":", "_")[:128]
    return f"{RATE_LIMIT_KEY_PREFIX}{scope}:{safe_ip}"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _check_ip_rate_limit_redis(
    ip: str,
    scope: str,
    *,
    max_requests: int,
    window_seconds: float,
) -> None:
    r = get_redis()
    scope_key = normalize_rate_limit_scope(scope)
    key = _redis_rate_limit_key(ip, scope_key)
    now_ms = _now_ms()
    window_ms = max(1, int(float(window_seconds) * 1000))
    cutoff_ms = now_ms - window_ms

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, "-inf", cutoff_ms)
    pipe.zcard(key)
    count = pipe.execute()[1]
    if int(count) >= max_requests:
        oldest = r.zrange(key, 0, 0, withscores=True)
        retry = int(window_seconds)
        if oldest:
            oldest_ms = int(oldest[0][1])
            retry = max(1, (oldest_ms + window_ms - now_ms) // 1000)
        raise ApiHttpError(
            CODE_RATE_LIMIT_EXCEEDED,
            f"{get_message(CODE_RATE_LIMIT_EXCEEDED)}，请 {retry} 秒后重试",
            http_status=429,
            headers={"Retry-After": str(retry)},
        )

    member = f"{now_ms}-{random.randint(1, 999)}"
    r.zadd(key, {member: now_ms})
    r.expire(key, int(max(window_seconds, 1)) + 1)


def _check_ip_rate_limit_memory(
    ip: str,
    scope: str,
    *,
    max_requests: int,
    window_seconds: float,
) -> None:
    scope_key = normalize_rate_limit_scope(scope)
    bucket = (ip, scope_key)
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        q = _buckets.setdefault(bucket, deque())
        while q and q[0] <= cutoff:
            q.popleft()
        if len(q) >= max_requests:
            retry = max(1, int(window_seconds - (now - q[0])))
            raise ApiHttpError(
                CODE_RATE_LIMIT_EXCEEDED,
                f"{get_message(CODE_RATE_LIMIT_EXCEEDED)}，请 {retry} 秒后重试",
                http_status=429,
                headers={"Retry-After": str(retry)},
            )
        q.append(now)


def check_ip_rate_limit(
    request: Request,
    *,
    max_requests: int,
    window_seconds: float,
    scope: str,
) -> None:
    if max_requests <= 0:
        return
    if not (scope or "").strip():
        raise ValueError("rate limit scope is required")
    ip = client_ip(request)
    scope_key = normalize_rate_limit_scope(scope)
    if redis_configured():
        try:
            _check_ip_rate_limit_redis(
                ip,
                scope_key,
                max_requests=max_requests,
                window_seconds=window_seconds,
            )
            return
        except ApiHttpError:
            raise
        except Exception:
            logger.warning(
                "redis rate limit failed, falling back to memory",
                exc_info=True,
            )
    _check_ip_rate_limit_memory(
        ip,
        scope_key,
        max_requests=max_requests,
        window_seconds=window_seconds,
    )


def ip_rate_limit(
    *,
    max_requests: int,
    window_seconds: float = 60.0,
    scope: str,
):
    """FastAPI 依赖：同一 IP 在 ``window_seconds`` 秒内最多 ``max_requests`` 次。"""

    normalize_rate_limit_scope(scope)

    def _dep(request: Request) -> None:
        check_ip_rate_limit(
            request,
            max_requests=max_requests,
            window_seconds=window_seconds,
            scope=scope,
        )

    return Depends(_dep)
