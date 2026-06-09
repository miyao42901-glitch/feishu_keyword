"""小红书接口 JSON → 统一列表。"""

from __future__ import annotations

import logging
from typing import Any

from social_platform.utils.coercion import extract_api_balance_cost
from social_platform.utils.duration import parse_duration
from social_platform.utils.time_ms import to_ms_timestamp
from social_platform.utils.worker_runtime import (
    split_exclude_needles,
    text_contains_any_needle,
)

logger = logging.getLogger(__name__)


class XhsParser:
    def parse(self, raw: dict[str, Any], *, exclude_words: str = "") -> dict[str, Any]:
        needles = split_exclude_needles(exclude_words)
        data = raw.get("data") or {}
        if not isinstance(data, dict):
            data = {}
        balance, cost = extract_api_balance_cost(raw, data=data)
        items = data.get("items") if isinstance(data, dict) else None
        if not items or not isinstance(items, list):
            logger.info("小红书返回空列表")
            return {
                "data": [],
                "balance": balance,
                "cost": cost,
                "error": None,
                "insufficient_balance": False,
            }

        rows: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            note = item.get("note")
            if not isinstance(note, dict):
                note = item

            title = note.get("title") or ""
            desc = note.get("desc") or ""
            display_title = title if title else desc or "无标题"
            display_desc = desc if desc else title

            if text_contains_any_needle(
                display_title, needles
            ) or text_contains_any_needle(display_desc, needles):
                continue

            note_id = note.get("id") or ""
            xsec = note.get("xsec_token") or ""
            if note_id and xsec:
                url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec}&xsec_source=pc_search"
            else:
                url = ""

            ctype = note.get("type", "unknown")

            duration_raw = note.get("video_duration", "0:00")
            video_duration = parse_duration(
                duration_raw
            )  # 视频时长（秒）：将 '0:36' 转换为 36
            has_music = note.get("has_music", False)
            images_list = [
                img.get("url", img.get("original"))
                for img in note.get("images_list") or []
                if isinstance(img, dict) and img.get("url", img.get("original"))
            ]
            stream = note.get("video_info_v2", {}).get("media", {}).get("stream", {})

            video_list = []

            # h264
            h264 = stream.get("h264", [])
            if len(h264) > 0 and isinstance(h264[0], dict):
                h264_url = h264[0].get("master_url")
                if h264_url:
                    video_list.append(h264_url)

            # h265[0]
            h265 = stream.get("h265", [])
            if len(h265) > 0 and isinstance(h265[0], dict):
                h265_url = h265[0].get("master_url")
                if h265_url:
                    video_list.append(h265_url)

            # h265[1]
            if len(h265) > 1 and isinstance(h265[1], dict):
                h265_url = h265[1].get("master_url")
                if h265_url:
                    video_list.append(h265_url)

            user_info = note.get("user") or {}
            if not isinstance(user_info, dict):
                user_info = {}
            nickname = user_info.get("nickname") or ""
            userid = user_info.get("userid") or ""
            avatar = user_info.get("images") or ""

            rows.append(
                {
                    "note_id": note_id,
                    "title": display_title,
                    "desc": display_desc,
                    "xsec_token": xsec,
                    "url": url,
                    "publish_time": to_ms_timestamp(
                        (note.get("timestamp") or 0) * 1000
                    ),
                    "like_count": int(note.get("liked_count", 0)),
                    "comment_count": int(note.get("comments_count", 0)),
                    "collect_count": int(note.get("collected_count", 0)),
                    "duration": video_duration,
                    "has_music": has_music,
                    "images_list": images_list,
                    "video_list": video_list,
                    "nickname": nickname,
                    "userid": userid,
                    "avatar": avatar,
                    "content_type": ctype,
                }
            )

        n_note = sum(1 for r in rows if r["content_type"] == "normal")
        n_video = sum(1 for r in rows if r["content_type"] == "video")
        logger.info(
            "小红书解析成功 条数=%s (图文=%s 视频=%s)", len(rows), n_note, n_video
        )

        return {
            "data": rows,
            "balance": balance,
            "cost": cost,
            "error": None,
            "insufficient_balance": False,
        }
