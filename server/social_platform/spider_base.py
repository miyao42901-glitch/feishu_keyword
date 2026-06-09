"""爬虫基类：HTTP + 注入的解析器（解析逻辑放在各 worker 的 parser 模块）。"""

from __future__ import annotations

import logging
from typing import Any, Optional, Protocol

from social_platform.http_client import BaseHttpClient, HttpClientError

logger = logging.getLogger(__name__)


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

    def _log_request(self, payload: dict[str, Any], *, attempt: int) -> None:
        logger.info(
            "%s request keyword=%r offset=%s page=%s cursor=%s cookies_len=%d attempt=%d",
            self.platform,
            payload.get("keyword"),
            payload.get("offset", ""),
            payload.get("page") or payload.get("currentPage", ""),
            payload.get("cursor", ""),
            len(str(payload.get("cookies_buffer") or "")),
            attempt + 1,
        )

    def _log_api_code(self, api_code: Any) -> None:
        logger.info("%s api_code=%s", self.platform, api_code)

    @staticmethod
    def _business_error_summary(raw: dict[str, Any]) -> str:
        msg = raw.get("msg") or raw.get("message") or ""
        return str(msg)[:200]

    def _network_error(self, exc: HttpClientError) -> dict[str, Any]:
        logger.warning("%s network_error: %s", self.platform, exc)
        return {
            "data": [],
            "balance": 0,
            "cost": 0,
            "error": {"origin": self.platform, "code": 5001, "msg": str(exc)},
            "insufficient_balance": False,
        }
