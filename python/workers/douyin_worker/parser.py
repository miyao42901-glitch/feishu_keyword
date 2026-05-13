"""抖音接口 JSON → 统一列表（仅处理业务已成功时的 body）。"""
from __future__ import annotations

import logging
from typing import Any

from social_platform.time_utils import to_ms_timestamp

logger = logging.getLogger(__name__)


class DouyinParser:
    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        remain_money = float(raw.get("remain_money", 0.0))
        inner = raw.get("data") or {}
        video_list = inner.get("data") or []
        if not isinstance(video_list, list):
            video_list = []

        extra = inner.get("extra") or {}
        logid = extra.get("logid", "") if isinstance(extra, dict) else ""
        cursor = inner.get("cursor", "")

        rows: list[dict[str, Any]] = []
        for item in video_list:
            if not isinstance(item, dict):
                continue
            aweme = item.get("aweme_info")
            if not isinstance(aweme, dict):
                continue
            aweme_id = aweme.get("aweme_id")
            if not aweme_id:
                continue
            desc = (aweme.get("desc") or "").strip()
            if not desc:
                continue
            stat = aweme.get("statistics") or {}
            if not isinstance(stat, dict):
                stat = {}
            rows.append(
                {
                    "title": desc or "无标题",
                    "summary": desc,
                    "url": f"https://www.douyin.com/jingxuan?modal_id={aweme_id}",
                    "origin": "抖音",
                    "publish_time": to_ms_timestamp(stat.get("create_time")),
                    "like_count": stat.get("digg_count", 0),
                    "comment_count": stat.get("comment_count", 0),
                    "share_count": stat.get("share_count", 0),
                    "collect_count": stat.get("collect_count", 0),
                }
            )

        logger.info("抖音解析成功，条数: %s", len(rows))
        return {
            "data": rows,
            "remain_money": remain_money,
            "error": None,
            "insufficient_balance": False,
            "next_cursor": cursor,
            "next_logid": logid,
        }
