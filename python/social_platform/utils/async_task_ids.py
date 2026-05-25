"""异步任务主键：URL 路径与字符串解析（BIGINT 自增）。"""

from __future__ import annotations

from typing import Optional


def parse_async_task_pk(raw: str) -> Optional[int]:
    s = (raw or "").strip()
    if not s.isdigit():
        return None
    n = int(s)
    return n if n > 0 else None
