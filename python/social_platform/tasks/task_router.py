"""历史 `normalize_social_payload` 已移除；异步任务请使用 `social_platform.actions.registry`。"""
from __future__ import annotations

from typing import Any


def normalize_social_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    兼容旧 Beat / 脚本：仍接受 `{action, params}`，供 `aggregated_job.run_task` 使用。
    新 HTTP 异步提交不再经过此函数。
    """
    action = str(payload.get("action") or "").strip()
    params = payload.get("params")
    if not isinstance(params, dict):
        params = {}
    if not action:
        raise ValueError("action is required")
    return {"action": action, "params": params}
