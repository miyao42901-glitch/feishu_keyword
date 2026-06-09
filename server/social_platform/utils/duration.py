"""时长解析 + HTML 清理工具。"""

from __future__ import annotations

import html
import re
from typing import Any


def parse_duration(duration_str: Any) -> int:
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


def parse_htmlstr_to_clean(s: Any) -> str:
    """去除 HTML 标签与实体，返回纯净文本（用于 title 等字段）。"""
    if s is None or not isinstance(s, str):
        return ""
    text = html.unescape(s)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()
