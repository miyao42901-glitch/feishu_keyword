"""抖音：业务码重试 + 调用 DouyinParser。"""

from __future__ import annotations

import logging
from typing import Any, Optional

from douyin_worker.parser import DouyinParser

from social_platform.api_status_codes import CODE_FAILED, CODE_INSUFFICIENT_BALANCE
from social_platform.http_client import BaseHttpClient, HttpClientError
from social_platform.spider_base import BaseSpider
from social_platform.utils.coercion import extract_api_balance_cost

logger = logging.getLogger(__name__)


class DouyinSpider(BaseSpider):
    def __init__(self, api_url: str, client: Optional[BaseHttpClient] = None) -> None:
        super().__init__(
            api_url, platform="douyin", parser=DouyinParser(), client=client
        )

    def orchestrate(
        self,
        payload: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        for attempt in range(3):
            self._log_request(payload, attempt=attempt)
            try:
                raw = self._client.post_json(self.api_url, payload, headers=headers)
            except HttpClientError as e:
                return self._network_error(e)

            api_code = raw.get("code")
            try:
                ac = int(api_code) if api_code is not None else None
            except (TypeError, ValueError):
                ac = None
            balance, cost = extract_api_balance_cost(raw)
            self._log_api_code(api_code)

            if ac == CODE_INSUFFICIENT_BALANCE:
                logger.warning("%s insufficient_balance balance=%s", self.platform, balance)
                return {
                    "data": [],
                    "balance": balance,
                    "cost": cost,
                    "error": None,
                    "insufficient_balance": True,
                    "next_cursor": payload.get("cursor", ""),
                    "next_logid": payload.get("log_id", ""),
                }
            if ac == CODE_FAILED:
                self._log_yddm_failed_response(raw, api_code=api_code)
                if attempt < 2:
                    continue
                break

            try:
                parsed = self._parser.parse(
                    raw,
                    exclude_words=str(payload.get("exclude_words") or ""),
                )
                logger.info(
                    "%s parsed rows=%d next_cursor=%s",
                    self.platform,
                    len(parsed.get("data") or []),
                    parsed.get("next_cursor", ""),
                )
                return parsed
            except Exception as e:  # noqa: BLE001
                logger.error("抖音解析异常: %s", e, exc_info=True)
                return {
                    "data": [],
                    "balance": balance,
                    "cost": cost,
                    "error": {
                        "origin": "douyin",
                        "code": 5000,
                        "msg": f"内部解析错误: {e!s}",
                    },
                    "insufficient_balance": False,
                    "next_cursor": "",
                    "next_logid": "",
                }

        logger.error("%s retries_exhausted", self.platform)
        return {
            "data": [],
            "balance": 0,
            "cost": 0,
            "error": {"origin": "douyin", "code": 5002, "msg": "重试机制异常"},
            "insufficient_balance": False,
            "next_cursor": "",
            "next_logid": "",
        }
