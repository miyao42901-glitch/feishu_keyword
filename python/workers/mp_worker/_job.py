"""公众号等场景复用的抖音检索 Worker 入口。"""
from __future__ import annotations

from typing import Any

from douyin_worker._job import _douyin_page_json_body, call_douyin_api
from http_api.constants import DOUYIN_GENERAL_URL
from social_platform.utils.worker_runtime import resolved_service_url, worker_meta

WORKER_NAME = "mp_worker"
WORKER_VERSION = "1.0.0"


def run_task(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    params = payload.get("params") or {}
    meta = worker_meta(WORKER_NAME, WORKER_VERSION)

    if action == "douyin_search_page":
        key, keyword = params.get("key"), params.get("keyword")
        if not key or not keyword:
            return {"ok": False, "error": "missing key or keyword", "meta": meta}
        url = resolved_service_url("DOUYIN_GENERAL_URL", DOUYIN_GENERAL_URL)
        if not url:
            return {"ok": False, "error": "DOUYIN_GENERAL_URL 为空", "meta": meta}
        raw = call_douyin_api(url, str(key).strip(), _douyin_page_json_body(params))
        ok = not raw.get("insufficient_balance") and raw.get("error") is None
        return {"ok": ok, "data": raw, "meta": meta}

    if action == "douyin_search_all":
        from douyin_worker._job import execute_douyin_search_all

        out = execute_douyin_search_all(params)
        out["meta"] = worker_meta(WORKER_NAME, WORKER_VERSION)
        return out

    return {
        "ok": False,
        "error": f"unsupported action: {action!r}；支持: douyin_search_page, douyin_search_all",
        "meta": meta,
    }
