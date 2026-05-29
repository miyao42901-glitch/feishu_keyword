"""小红书：业务码重试 + XhsParser。"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from xhs_worker.parser import XhsParser

from social_platform.api_status_codes import CODE_FAILED, CODE_INSUFFICIENT_BALANCE
from social_platform.http_client import BaseHttpClient, HttpClientError
from social_platform.spider_base import BaseSpider

logger = logging.getLogger(__name__)


class XhsSpider(BaseSpider):
    def __init__(self, api_url: str, client: Optional[BaseHttpClient] = None) -> None:
        super().__init__(api_url, platform="xhs", parser=XhsParser(), client=client)

    def orchestrate(
        self,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        for attempt in range(3):
            try:
                raw = self._client.post_json(self.api_url, payload, headers=headers)
            except HttpClientError as e:
                return self._network_error(e)

            api_code = raw.get("code")
            try:
                ac = int(api_code) if api_code is not None else None
            except (TypeError, ValueError):
                ac = None
            balance = float(raw.get("balance", 0.0))
            logger.info("小红书 业务码=%s", api_code)

            if ac == CODE_INSUFFICIENT_BALANCE:
                return {
                    "data": [],
                    "balance": balance,
                    "error": None,
                    "insufficient_balance": True,
                }

            if ac == CODE_FAILED:
                msg = raw.get("msg", "Unknown error")
                logger.warning("小红书业务错误: %s %s", ac, msg)
                if attempt < 2:
                    continue
                return {
                    "data": [],
                    "balance": balance,
                    "error": {"origin": "xhs", "code": ac, "msg": msg},
                    "insufficient_balance": False,
                }

            try:
                return self._parser.parse(
                    raw,
                    exclude_words=str(payload.get("exclude_words") or ""),
                )
            except Exception as e:  # noqa: BLE001
                logger.error("小红书解析异常: %s", e, exc_info=True)
                return {
                    "data": [],
                    "balance": float(raw.get("balance", 0.0)),
                    "error": {
                        "origin": "xhs",
                        "code": 5000,
                        "msg": f"内部解析错误: {e!s}",
                    },
                    "insufficient_balance": False,
                }

        return {
            "data": [],
            "balance": 0.0,
            "error": {"origin": "xhs", "code": 5002, "msg": "重试机制异常"},
            "insufficient_balance": False,
        }
