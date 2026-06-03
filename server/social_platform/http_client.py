"""HTTP：POST JSON。同步 ``post_json``（requests）供 Spider/Celery；``post_json_async``（aiohttp）供 async 路径。"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional
from uuid import uuid4

import aiohttp
import requests
from requests import RequestException

logger = logging.getLogger(__name__)


class HttpClientError(Exception):
    """网络层重试用尽或响应非 JSON。"""


def _resolve_platform_from_url(url: str) -> Optional[str]:
    url_lower = url.lower()
    if "douyin" in url_lower:
        return "douyin"
    if "xhs" in url_lower or "xiaohongshu" in url_lower:
        return "xhs"
    if "weixin" in url_lower or "wechat" in url_lower or "wx" in url_lower:
        return "wx"
    if "mp" in url_lower:
        return "mp"
    return None


def _track_api_call(
    *,
    request_id: str,
    url: str,
    result: str,
    error_code: Optional[str],
    latency_ms: int,
) -> None:
    try:
        from social_platform.api_call_context import get_api_call_context
        ctx = get_api_call_context()
        if ctx is None:
            return
        db = ctx.get("db")
        if db is None:
            return
        from social_platform.services import analytics_service
        platform = ctx.get("platform") or _resolve_platform_from_url(url)
        analytics_service.write_api_call(
            db,
            request_id=request_id,
            task_id=ctx.get("task_id"),
            exec_id=ctx.get("exec_id"),
            platform=platform,
            result=result,
            error_code=error_code,
            latency_ms=latency_ms,
        )
    except Exception:
        logger.debug("analytics api_call tracking failed", exc_info=True)


class BaseHttpClient:
    def __init__(
        self,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_sleep_sec: float = 1.0,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_sleep_sec = retry_sleep_sec

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        同步 POST JSON（requests）。
        供 Spider、Celery gevent worker、FastAPI ``def`` 同步路由使用；勿在 ``async def`` 中直接调用。
        """
        last_exc: Optional[Exception] = None
        req_headers = dict(headers or {})
        request_id = uuid4().hex
        t0 = time.monotonic()
        for attempt in range(self.max_retries):
            try:
                logger.debug("HTTP POST url=%s payload=%s", url, payload)
                resp = requests.post(
                    url,
                    json=payload,
                    headers=req_headers,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise HttpClientError(f"响应 JSON 非对象: {type(data)!s}")
                latency = int((time.monotonic() - t0) * 1000)
                _track_api_call(
                    request_id=request_id,
                    url=url,
                    result="成功",
                    error_code=None,
                    latency_ms=latency,
                )
                return data
            except (RequestException, ValueError, TypeError) as e:
                last_exc = e
                logger.warning(
                    "HTTP POST 失败 (%s/%s): %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_sleep_sec)
        latency = int((time.monotonic() - t0) * 1000)
        _track_api_call(
            request_id=request_id,
            url=url,
            result="失败",
            error_code="network_error",
            latency_ms=latency,
        )
        raise HttpClientError(
            f"POST 重试{self.max_retries}次仍失败: {last_exc!s}"
        ) from last_exc

    async def post_json_async(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """异步 POST JSON（aiohttp）；在已有事件循环的 async 代码路径中使用。"""
        client_timeout = aiohttp.ClientTimeout(total=self.timeout)
        last_exc: Optional[Exception] = None
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            for attempt in range(self.max_retries):
                try:
                    logger.debug("HTTP POST url=%s payload=%s", url, payload)
                    async with session.post(
                        url, json=payload, headers=headers
                    ) as resp:
                        resp.raise_for_status()
                        data = await resp.json(content_type=None)
                        if not isinstance(data, dict):
                            raise HttpClientError(f"响应 JSON 非对象: {type(data)!s}")
                        return data
                except (
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    ValueError,
                    TypeError,
                ) as e:
                    last_exc = e
                    logger.warning(
                        "HTTP POST 失败 (%s/%s): %s",
                        attempt + 1,
                        self.max_retries,
                        e,
                        exc_info=logger.isEnabledFor(logging.DEBUG),
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_sleep_sec)
        raise HttpClientError(
            f"POST 重试{self.max_retries}次仍失败: {last_exc!s}"
        ) from last_exc

