"""抖音接口 JSON → 统一列表（仅处理业务已成功时的 body）。"""
from __future__ import annotations

import logging
from typing import Any

from social_platform.utils.time_ms import to_ms_timestamp
from social_platform.utils.worker_runtime import split_exclude_needles, text_contains_any_needle

logger = logging.getLogger(__name__)


class DouyinParser:
    def parse(self, raw: dict[str, Any], *, exclude_words: str = "") -> dict[str, Any]:
        needles = split_exclude_needles(exclude_words)
        data = raw.get("data") or {}
        balance = float(data.get("balance", 0.0))
        inner = raw.get("data") or {}
        items_list = inner.get("data") or []

        if not isinstance(items_list, list):
            items_list = []

        extra = inner.get("extra") or {}
        logid = extra.get("logid", "") if isinstance(extra, dict) else ""
        cursor = inner.get("cursor", "")

        rows: list[dict[str, Any]] = []

        for item in items_list:
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

            title = desc or "无标题"

            if text_contains_any_needle(title, needles) or text_contains_any_needle(desc, needles):
                continue

            # 作者
            author = aweme.get("author") or {}
            if not isinstance(author, dict):
                author = {}

            # 视频
            video = aweme.get("video") or {}
            if not isinstance(video, dict):
                video = {}

            # 统计
            stat = aweme.get("statistics") or {}
            if not isinstance(stat, dict):
                stat = {}

            # 昵称
            nickname = author.get("nickname", "")

            # 签名
            signature = author.get("signature", "")

            # 头像
            avatar = (
                author.get("avatar_larger", {})
                .get("url_list", [""])[0]
            )

            # 企业认证
            enterprise_verify_reason = author.get(
                "enterprise_verify_reason",
                ""
            )

            # 时长（接口是毫秒）
            duration = round(video.get("duration", 0) / 1000, 2)

            # 封面
            cover = (
                video.get("cover", {})
                .get("url_list", [""])[0]
            )

            # sec_uid
            user_id = author.get("sec_uid", "")

            # 无水印播放地址
            play_addr = (
                video.get("play_addr", {})
                .get("url_list", [])
            )

        
            rows.append(
                {
                    "title": title,
                    "aweme_id": aweme_id,
                    "desc": desc,

                    "url": f"https://www.douyin.com/video/{aweme_id}",

                    # 作者
                    "nickname": nickname,
                    "signature": signature,
                    "avatar": avatar,
                    "user_id": user_id,
                    "verify_name": enterprise_verify_reason,

                    # 视频
                    "cover": cover,
                    "duration": duration,

                    # 视频地址
                    "video_list": play_addr,

                    # 数据
                    "publish_time": to_ms_timestamp(
                        aweme.get("create_time")
                    ),

                    "like_count": stat.get("digg_count", 0),
                    "comment_count": stat.get("comment_count", 0),
                    "share_count": stat.get("share_count", 0),
                    "collect_count": stat.get("collect_count", 0),
                }
            )

        logger.info("抖音解析成功，条数: %s", len(rows))

        return {
            "data": rows,
            "balance": balance,
            "error": None,
            "insufficient_balance": False,
            "next_cursor": cursor,
            "next_logid": logid,
        }