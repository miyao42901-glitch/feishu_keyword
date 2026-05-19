"""时间戳归一化（毫秒）。"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any


def to_ms_timestamp(time_str: Any) -> int:
    if time_str is None:
        return int(time.time() * 1000)

    if isinstance(time_str, (int, float)):
        if time_str > 1e12:
            return int(time_str)
        return int(time_str * 1000)

    if isinstance(time_str, str):
        if time_str.isdigit():
            ts = int(time_str)
            return ts if ts > 1e12 else ts * 1000
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return int(datetime.strptime(time_str, fmt).timestamp() * 1000)
            except (ValueError, TypeError):
                continue
        return int(time.time() * 1000)

    return int(time.time() * 1000)
