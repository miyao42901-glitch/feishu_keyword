"""小红书接口 JSON → 统一列表。"""
from __future__ import annotations

import logging
from typing import Any

from social_platform.utils.time_ms import to_ms_timestamp
from social_platform.utils.worker_runtime import split_exclude_needles, text_contains_any_needle

logger = logging.getLogger(__name__)


class XhsParser:
    def parse(self, raw: dict[str, Any], *, exclude_words: str = "") -> dict[str, Any]:
        needles = split_exclude_needles(exclude_words)
        data = raw.get("data") or {}
        balance = float(data.get("balance", 0.0))
        items = data.get("items") if isinstance(data, dict) else None
        if not items or not isinstance(items, list):
            logger.info("小红书返回空列表")
            return {
                "data": [],
                "balance": balance,
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

            if text_contains_any_needle(display_title, needles) or text_contains_any_needle(display_desc, needles):
                continue

            note_id = note.get("id") or ""
            xsec = note.get("xsec_token") or ""
            if note_id and xsec:
                url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec}&xsec_source=pc_search"
            else:
                url = ""

            ctype = note.get("type", "unknown")

            def parse_duration(duration_str):
                """将视频时长转换为秒，支持：
                '0:36'
                '12:30'
                '01:02:03'
                '36'
                36
                """

                if duration_str is None:
                    return 0

                # 数字直接返回
                if isinstance(duration_str, (int, float)):
                    return int(duration_str)

                # 非字符串返回0
                if not isinstance(duration_str, str):
                    return 0

                duration_str = duration_str.strip()

                if not duration_str:
                    return 0

                try:
                    # 时间格式
                    if ":" in duration_str:
                        parts = list(map(int, duration_str.split(":")))

                        # MM:SS
                        if len(parts) == 2:
                            minutes, seconds = parts
                            return minutes * 60 + seconds

                        # HH:MM:SS
                        elif len(parts) == 3:
                            hours, minutes, seconds = parts
                            return hours * 3600 + minutes * 60 + seconds

                        return 0

                    # 纯数字字符串
                    return int(duration_str)

                except Exception:
                    return 0

            duration_raw = note.get("video_duration", "0:00")
            video_duration = parse_duration(duration_raw)  # 视频时长（秒）：将 '0:36' 转换为 36
            has_music = note.get("has_music", False)
            images_list = [item.get("url", item.get("original")) for item in note.get("images_list") or [] if item.get("url", item.get("original"))]
            # video_url = note.get("video_info_v2", {}).get("media", {}).get("stream", {}).get("h264", [{}])[0].get("master_url")
            # data.items[0].note['video_info_v2'].media.stream.h264[0]['master_url']
            # data.items[0].note['video_info_v2'].media.stream.h265[0]['master_url']
            # data.items[0].note['video_info_v2'].media.stream.h265[1]['master_url']
            stream = note.get("video_info_v2", {}) \
             .get("media", {}) \
             .get("stream", {})

            video_list = []

            # h264
            h264 = stream.get("h264", [])
            if len(h264) > 0 and isinstance(h264[0], dict):
                url = h264[0].get("master_url")
                if url:
                    video_list.append(url)

            # h265[0]
            h265 = stream.get("h265", [])
            if len(h265) > 0 and isinstance(h265[0], dict):
                url = h265[0].get("master_url")
                if url:
                    video_list.append(url)

            # h265[1]
            if len(h265) > 1 and isinstance(h265[1], dict):
                url = h265[1].get("master_url")
                if url:
                    video_list.append(url)

            user_info = note.get("user") or {}
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
                    "publish_time": to_ms_timestamp((note.get("timestamp") or 0) * 1000),
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
        logger.info("小红书解析成功 条数=%s (图文=%s 视频=%s)", len(rows), n_note, n_video)

        return {
            "data": rows,
            "balance": balance,
            "error": None,
            "insufficient_balance": False,
        }
