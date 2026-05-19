"""视频号 Spider：调用 SHIPINHAO_GENERAL_URL + WxVideoParser。"""

from __future__ import annotations

import logging
from typing import Any, Optional

from wxvideo_worker.parser import WxVideoParser

from social_platform.api_status_codes import CODE_FAILED, CODE_INSUFFICIENT_BALANCE
from social_platform.http_client import BaseHttpClient, HttpClientError
from social_platform.spider_base import BaseSpider

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
            logger.info("视频号 payload: %s", payload)
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
            balance = float(raw.get("balance", 0.0))
            logger.info("视频号 业务码=%s", api_code)

            if ac == CODE_INSUFFICIENT_BALANCE:
                return {
                    "data": [],
                    "balance": balance,
                    "error": None,
                    "insufficient_balance": True,
                    "next_offset": payload.get("offset", ""),
                    "cookies_buffer": payload.get("cookies_buffer", ""),
                }
            if ac == CODE_FAILED:
                logger.warning("视频号 业务错误: %s", raw)
                if attempt < 2:
                    continue
                break

            try:
                return self._parser.parse(
                    raw,
                    exclude_words=str(payload.get("exclude_words") or ""),
                )
            except Exception as e:  # noqa: BLE001
                logger.error("视频号解析异常: %s", e, exc_info=True)
                return {
                    "data": [],
                    "balance": balance,
                    "error": {
                        "origin": "wxvideo",
                        "code": 5000,
                        "msg": f"内部解析错误: {e!s}",
                    },
                    "insufficient_balance": False,
                    "next_offset": "",
                    "cookies_buffer": "",
                }

        return {
            "data": [],
            "balance": 0.0,
            "error": {"origin": "wxvideo", "code": 5002, "msg": "重试机制异常"},
            "insufficient_balance": False,
            "next_offset": "",
            "cookies_buffer": "",
        }
