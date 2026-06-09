"""视频号 Spider：调用 WXVIDEO_GENERAL_URL + WxVideoParser。"""

from __future__ import annotations

import logging
from typing import Any, Optional

from wxvideo_worker.parser import WxVideoParser

from social_platform.api_status_codes import CODE_FAILED, CODE_INSUFFICIENT_BALANCE
from social_platform.http_client import BaseHttpClient, HttpClientError
from social_platform.spider_base import BaseSpider
from social_platform.utils.coercion import extract_api_balance_cost

logger = logging.getLogger(__name__)


class WxVideoSpider(BaseSpider):
    def __init__(self, api_url: str, client: Optional[BaseHttpClient] = None) -> None:
        super().__init__(
            api_url, platform="wxvideo", parser=WxVideoParser(), client=client
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
                api_payload = {k: v for k, v in payload.items() if k != "exclude_words"}
                raw = self._client.post_json(self.api_url, api_payload, headers=headers)
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
                    "next_offset": payload.get("offset", ""),
                    "cookies_buffer": payload.get("cookies_buffer", ""),
                }
            if ac == CODE_FAILED:
                logger.warning(
                    "%s business_error code=%s msg=%s",
                    self.platform,
                    api_code,
                    self._business_error_summary(raw),
                )
                if attempt < 2:
                    continue
                break

            try:
                parsed = self._parser.parse(
                    raw,
                    exclude_words=str(payload.get("exclude_words") or ""),
                )
                logger.info(
                    "%s parsed rows=%d next_offset=%s cookies_len=%d",
                    self.platform,
                    len(parsed.get("data") or []),
                    parsed.get("next_offset", ""),
                    len(str(parsed.get("cookies_buffer") or "")),
                )
                return parsed
            except Exception as e:  # noqa: BLE001
                logger.error("视频号解析异常: %s", e, exc_info=True)
                return {
                    "data": [],
                    "balance": balance,
                    "cost": cost,
                    "error": {
                        "origin": "wxvideo",
                        "code": 5000,
                        "msg": f"内部解析错误: {e!s}",
                    },
                    "insufficient_balance": False,
                    "next_offset": "",
                    "cookies_buffer": "",
                }

        logger.error("%s retries_exhausted", self.platform)
        return {
            "data": [],
            "balance": 0,
            "cost": 0,
            "error": {"origin": "wxvideo", "code": 5002, "msg": "重试机制异常"},
            "insufficient_balance": False,
            "next_offset": "",
            "cookies_buffer": "",
        }
