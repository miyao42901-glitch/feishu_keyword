"""小红书接口 JSON → 统一列表。"""
from __future__ import annotations

import logging
from typing import Any

from social_platform.time_utils import to_ms_timestamp

logger = logging.getLogger(__name__)


class XhsParser:
    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        remain_money = float(raw.get("remain_money", 0.0))
        data = raw.get("data") or {}
        items = data.get("items") if isinstance(data, dict) else None
        if not items or not isinstance(items, list):
            logger.info("小红书返回空列表")
            return {
                "data": [],
                "remain_money": remain_money,
                "error": None,
                "insufficient_balance": False,
            }

        rows: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            note = item.get("note")
            if not isinstance(note, dict):
                continue

            title = note.get("title") or ""
            desc = note.get("desc") or ""
            display_title = title if title else desc
            display_desc = desc if desc else title
            if not display_title and not display_desc:
                continue

            item_id = note.get("id") or ""
            xsec = note.get("xsec_token") or ""
            if item_id and xsec:
                url = f"https://www.xiaohongshu.com/explore/{item_id}?xsec_token={xsec}&xsec_source=pc_search"
            else:
                url = ""

            ctype = note.get("type", "unknown")
            rows.append(
                {
                    "title": display_title,
                    "summary": display_desc,
                    "url": url,
                    "origin": "小红书",
                    "publish_time": to_ms_timestamp((note.get("timestamp") or 0) * 1000),
                    "like_count": int(note.get("liked_count", 0)),
                    "comment_count": int(note.get("comments_count", 0)),
                    "share_count": 0,
                    "collect_count": int(note.get("collected_count", 0)),
                    "content_type": ctype,
                }
            )

        n_note = sum(1 for r in rows if r["content_type"] == "normal")
        n_video = sum(1 for r in rows if r["content_type"] == "video")
        logger.info("小红书解析成功 条数=%s (图文=%s 视频=%s)", len(rows), n_note, n_video)

        return {
            "data": rows,
            "remain_money": remain_money,
            "error": None,
            "insufficient_balance": False,
        }
