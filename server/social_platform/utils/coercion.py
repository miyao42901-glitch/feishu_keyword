from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def as_third_party_str(v: Any) -> str:
    """None → 空串，其余 `str(v)`。"""
    if v is None:
        return ""
    return str(v)


def optional_body_str(params: dict[str, Any], *keys: str) -> Optional[str]:
    """参数显式存在且去空白后非空时返回字符串，否则 ``None``。"""
    for key in keys:
        if key not in params:
            continue
        value = params.get(key)
        if value is None:
            continue
        text = as_third_party_str(value).strip()
        if text:
            return text
    return None


def optional_body_int(params: dict[str, Any], *keys: str) -> Optional[int]:
    """参数显式存在且可解析为 int 时返回，否则 ``None``。"""
    for key in keys:
        if key not in params:
            continue
        value = params.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def as_api_int(v: Any, default: int = 0) -> int:
    """上游 monitor 数值字段（如 balance、cost）→ int。"""
    if v is None:
        return default
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def accumulate_search_all_balance_cost(
    *,
    total_cost: int,
    last_balance: int,
    page_result: dict[str, Any],
) -> tuple[int, int]:
    """search-all 多页：cost 为各页之和；balance 取最后一次上游返回值。"""
    page_balance = page_result.get("balance")
    if page_balance is not None:
        last_balance = as_api_int(page_balance, last_balance)
    total_cost += as_api_int(page_result.get("cost"), 0)
    return total_cost, last_balance


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
