"""按 action 前缀将任务转发到 douyin_worker / xhs_worker（原 jzl_social 逻辑）。"""
from __future__ import annotations

from typing import Any

from social_platform.utils.worker_runtime import worker_meta

WORKER_NAME = "jzl_social"
WORKER_VERSION = "1.0.0"


def _merge_meta(out: dict[str, Any]) -> dict[str, Any]:
    base = worker_meta(WORKER_NAME, WORKER_VERSION)
    inner = out.pop("meta", {})
    out["meta"] = {**inner, **base}
    return out


def run_task(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "")

    if action.startswith("douyin_"):
        from douyin_worker._job import run_task as run_douyin

        return _merge_meta(run_douyin(payload))

    if action.startswith("xhs_"):
        from xhs_worker._job import run_task as run_xhs

        return _merge_meta(run_xhs(payload))

    return {
        "ok": False,
        "error": (
            f"unsupported action: {action!r}；"
            "支持: douyin_search_page, douyin_search_all, xhs_search_page, xhs_search_all"
        ),
        "meta": worker_meta(WORKER_NAME, WORKER_VERSION),
    }
