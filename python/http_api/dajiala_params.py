"""调用大加拉等下游前：将对外 `X-API-KEY` 规范为 Worker 使用的 `key`。"""
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
