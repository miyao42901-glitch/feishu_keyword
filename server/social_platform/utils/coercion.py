from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def as_third_party_str(v: Any) -> str:
    """None → 空串，其余 `str(v)`。"""
    if v is None:
        return ""
    return str(v)


def as_api_int(v: Any, default: int = 0) -> int:
    """上游 monitor 数值字段（如 balance、cost）→ int。"""
    if v is None:
        return default
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def extract_api_balance_cost(
    raw: dict[str, Any], *, data: dict[str, Any] | None = None
) -> tuple[int, int]:
    """从上游 JSON 提取 balance、cost（优先 data 内，回退 raw 顶层）。"""
    inner = data if data is not None else raw.get("data")
    if not isinstance(inner, dict):
        inner = {}
    balance = as_api_int(inner.get("balance", raw.get("balance", 0)))
    cost = as_api_int(inner.get("cost", raw.get("cost", 0)))
    return balance, cost


def extract_cookies_buffer(data: dict[str, Any]) -> str:
    """从 ``data['cookies']`` JSON 字符串解析 ``cookies_buffer``。"""
    cookies_raw = data.get("cookies")
    if cookies_raw is None:
        return ""
    try:
        if isinstance(cookies_raw, str):
            parsed = json.loads(cookies_raw)
        elif isinstance(cookies_raw, dict):
            parsed = cookies_raw
        else:
            return ""
        if not isinstance(parsed, dict):
            return ""
        return as_third_party_str(parsed.get("cookies_buffer"))
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.debug("extract_cookies_buffer failed: %s", e)
        return ""
