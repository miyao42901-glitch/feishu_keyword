"""调用大加拉等下游前：参数字典规范化（如 X-API-KEY → key、去掉空字符串字段）。"""

from __future__ import annotations

from typing import Any


def to_worker_params(client_params: dict[str, Any]) -> dict[str, Any]:
    """若存在 `X-API-KEY` 且未显式提供非空 `key`，则写入 `key`；`X-API-KEY` 不会传给 Worker。"""
    p = dict(client_params or {})
    if "X-API-KEY" in p:
        v = str(p.pop("X-API-KEY")).strip()
        if v and not str(p.get("key", "")).strip():
            p["key"] = v
    return p


def prune_empty_string_fields(obj: Any) -> Any:
    """
    递归去掉值为空字符串 `""` 的键；嵌套 dict 若被删空则整键省略。
    用于 `body_json` 仅存非空字符串字段（其它类型原样保留）。
    """
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            pv = prune_empty_string_fields(v)
            if pv == "":
                continue
            if isinstance(pv, dict) and not pv:
                continue
            out[k] = pv
        return out
    if isinstance(obj, list):
        return [prune_empty_string_fields(x) for x in obj]
    return obj
