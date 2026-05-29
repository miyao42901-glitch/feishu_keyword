"""视频号接口 JSON → 统一列表（解析 subBoxes/items 及 report_extinfo_str）。"""

from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Any

from social_platform.utils.duration import parse_duration, parse_htmlstr_to_clean
from social_platform.utils.time_ms import to_ms_timestamp
from social_platform.utils.worker_runtime import (
    split_exclude_needles,
    text_contains_any_needle,
)

logger = logging.getLogger(__name__)


def _decode_report_extinfo_by_url(report_str: str) -> dict[str, Any]:
    """URL 解码 report_extinfo_str JSON，提取统计数字。"""
    if not report_str or not isinstance(report_str, str):
        return {}
    try:
        # URL 解码
        decoded = urllib.parse.unquote(report_str)

        # 解析 JSON
        data = json.loads(decoded)
    except Exception as e:
        print(f"Exception: {e}")
        try:
            # 兼容双重编码的情况
            decoded = urllib.parse.unquote(urllib.parse.unquote(report_str))
            data = json.loads(decoded)
        except Exception:
            return {}

    if isinstance(data, dict):
        return data
    return {}


class WxVideoParser:
    def parse(self, raw: dict[str, Any], *, exclude_words: str = "") -> dict[str, Any]:
        needles = split_exclude_needles(exclude_words)
        data = raw.get("data") or {}
        balance = float(data.get("balance", raw.get("balance", 0.0)))

        # 目标结构：data.data[i].subBoxes[j].items[k]
        root_data = data.get("data") or []
        if not isinstance(root_data, list):
            root_data = []

        rows: list[dict[str, Any]] = []
        for block in root_data:
            if not isinstance(block, dict):
                continue
            sub_boxes = block.get("subBoxes") or []
            if not isinstance(sub_boxes, list):
                continue
            for sub in sub_boxes:
                if not isinstance(sub, dict):
                    continue
                items = sub.get("items") or []
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue

                    # 提取指定字段
                    export_id = item.get("exportId") or ""
                    if not export_id:
                        continue

                    title = parse_htmlstr_to_clean(item.get("title")) or "无标题"
                    if text_contains_any_needle(title, needles):
                        continue
                    time_raw = item.get("pubTime") or item.get("dateTime") or ""
                    publish_time_ms = to_ms_timestamp(time_raw)
                    duration_val = parse_duration(item.get("duration"))
                    image = item.get("image") or ""
                    video_url = item.get("videoUrl") or ""

                    source = item.get("source") or {}
                    if not isinstance(source, dict):
                        source = {}
                    nickname = source.get("title") or ""
                    avatar_url = source.get("iconUrl") or ""

                    # 解码统计
                    report_str = item.get("report_extinfo_str") or ""
                    stats = _decode_report_extinfo_by_url(report_str)
                    like_cnt = stats.get("like_cnt", 0)
                    thumb_cnt = stats.get("thumb_cnt", 0)
                    forward_cnt = stats.get("forward_cnt", 0)
                    comment_cnt = stats.get("comment_cnt", 0)

                    row = {
                        "post_id": str(export_id),
                        "title": title,
                        "publish_time": publish_time_ms,
                        "duration": duration_val,
                        "cover_url": image,
                        "video_url": video_url,
                        "nickname": nickname,
                        "avatar_url": avatar_url,
                        "like_count": like_cnt,
                        "thumb_count": thumb_cnt,
                        "forward_count": forward_cnt,
                        "comment_count": comment_cnt,
                    }
                    rows.append(row)

        return {
            "data": rows,
            "balance": balance,
            "error": None,
            "insufficient_balance": False,
            "next_offset": data.get("offset", ""),
            "cookies_buffer": data.get("cookies_buffer", ""),
            "total": len(rows),
        }
