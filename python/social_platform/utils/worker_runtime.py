"""Worker 任务共用：meta、环境 URL、鉴权头名、排除词解析等。"""
from __future__ import annotations

import os
from typing import Any

API_KEY_HEADER = "X-API-Key"


def worker_meta(worker: str, version: str) -> dict[str, str]:
    return {"worker": worker, "version": version}


def resolved_service_url(env_key: str, default_url: str) -> str:
    return (os.environ.get(env_key) or default_url).strip()


def split_exclude_needles(exclude_words: str) -> list[str]:
    """空格分隔的排除词 → 非空片段列表（各平台解析可复用）。"""
    return [p.strip() for p in (exclude_words or "").split(" ") if p.strip()]


def text_contains_any_needle(text: Any, needles: list[str]) -> bool:
    """`text` 中是否包含任一子串 `needles`（无词则永不命中）。"""
    if not needles:
        return False
    s = "" if text is None else str(text)
    return any(n in s for n in needles)
