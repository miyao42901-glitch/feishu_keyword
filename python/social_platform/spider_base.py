"""爬虫基类：HTTP + 注入的解析器（解析逻辑放在各 worker 的 parser 模块）。"""
from __future__ import annotations

from typing import Any, Optional, Protocol

from social_platform.http_client import BaseHttpClient, HttpClientError


class ResponseParser(Protocol):
    def parse(self, raw: dict[str, Any]) -> dict[str, Any]: ...


class BaseSpider:
    def __init__(
        self,
        api_url: str,
        *,
        platform: str,
        parser: ResponseParser,
        client: Optional[BaseHttpClient] = None,
    ) -> None:
        self.api_url = api_url
        self.platform = platform
        self._parser = parser
        self._client = client or BaseHttpClient()

    def orchestrate(
        self,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        try:
            raw = self._client.post_json(self.api_url, payload, headers=headers)
        except HttpClientError as e:
            return self._network_error(e)
        return self._parser.parse(raw)

    def run(
        self,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        return self.orchestrate(payload, headers=headers)

    def _network_error(self, exc: HttpClientError) -> dict[str, Any]:
        return {
            "data": [],
            "remain_money": 0.0,
            "error": {"origin": self.platform, "code": 5001, "msg": str(exc)},
            "insufficient_balance": False,
        }
