"""HTTP：POST JSON、超时、aiohttp 异步 IO + 同步封装 post_json。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class HttpClientError(Exception):
    """网络层重试用尽或响应非 JSON。"""


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

    async def post_json_async(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        client_timeout = aiohttp.ClientTimeout(total=self.timeout)
        last_exc: Optional[Exception] = None
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            for attempt in range(self.max_retries):
                try:
                    print(f"url: {url}")
                    print(f"payload: {payload}")
                    async with session.post(url, json=payload, headers=headers) as resp:
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
                        "HTTP POST 失败 (%s/%s): %s", attempt + 1, self.max_retries, e
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_sleep_sec)
        raise HttpClientError(
            f"POST 重试{self.max_retries}次仍失败: {last_exc!s}"
        ) from last_exc

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """供同步爬虫调用；内部 asyncio.run，请勿在已有运行中的事件循环里调用。"""
        return asyncio.run(self.post_json_async(url, payload, headers=headers))
