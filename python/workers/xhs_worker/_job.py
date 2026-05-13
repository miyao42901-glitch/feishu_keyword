"""小红书 Worker 任务入口。"""
from __future__ import annotations

import os
from typing import Any

from social_platform.urls import XHS_GENERAL_URL
from xhs_worker.spider import XhsSpider

WORKER_NAME = "xhs_worker"
WORKER_VERSION = "1.0.0"

_API_KEY_HEADER = "X-API-Key"


def _api_url() -> str:
    return (os.environ.get("XHS_GENERAL_URL") or XHS_GENERAL_URL).strip()


def _as_third_party_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _third_party_json_body(params: dict[str, Any]) -> dict[str, Any]:
    cursor = str(params.get("cursor") or "")
    if not cursor.strip():
        cursor = str(params.get("page") or "")
    return {
        "keyword": str(params.get("keyword") or ""),
        "cursor": cursor,
        "log_id": str(params.get("log_id") or params.get("logid") or ""),
        "sort_type": _as_third_party_str(params.get("sort_type")),
        "publish_time": _as_third_party_str(params.get("publish_time")),
        "filter_duration": _as_third_party_str(params.get("filter_duration")),
        "content_type": _as_third_party_str(params.get("content_type")),
    }


def _xhs_body_for_page(params: dict[str, Any]) -> dict[str, Any]:
    """单页：空 cursor 视为第一页 `"1\"`。"""
    body = _third_party_json_body(params)
    if not str(body.get("cursor") or "").strip():
        body["cursor"] = "1"
    return body


def call_xhs_api(api_url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:
    return XhsSpider(api_url).run(body, headers={_API_KEY_HEADER: key.strip()})


def fetch_xhs_all(api_url: str, key: str, params: dict[str, Any], max_pages: int) -> dict[str, Any]:
    all_data: list[Any] = []
    remain_money = 0.0
    insufficient_balance = False
    last_error = None

    base = _third_party_json_body(params)
    c0 = str(base.get("cursor") or "").strip()
    start = int(c0) if c0.isdigit() else 1

    for i in range(max_pages):
        body = dict(base)
        body["cursor"] = str(start + i)
        result = call_xhs_api(api_url, key, body)
        if result.get("insufficient_balance"):
            insufficient_balance = True
            break
        if result.get("error"):
            last_error = result["error"]
            break
        data = result.get("data", [])
        if not data:
            break
        all_data.extend(data)
        remain_money = result.get("remain_money", remain_money)

    return {
        "records": all_data,
        "remain_money": remain_money,
        "insufficient_balance": insufficient_balance,
        "last_error": last_error,
    }


def _meta() -> dict[str, str]:
    return {"worker": WORKER_NAME, "version": WORKER_VERSION}


def run_task(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    params = payload.get("params") or {}
    meta = _meta()

    if action == "xhs_search_page":
        key, keyword = params.get("key"), params.get("keyword")
        if not key or not keyword:
            return {"ok": False, "error": "missing key or keyword", "meta": meta}
        url = _api_url()
        if not url:
            return {"ok": False, "error": "XHS_GENERAL_URL 为空", "meta": meta}
        raw = call_xhs_api(url, str(key).strip(), _xhs_body_for_page(params))
        ok = not raw.get("insufficient_balance") and raw.get("error") is None
        return {"ok": ok, "data": raw, "meta": meta}

    if action == "xhs_search_all":
        key, keyword = params.get("key"), params.get("keyword")
        if not key or not keyword:
            return {"ok": False, "error": "missing key or keyword", "meta": meta}
        url = _api_url()
        if not url:
            return {"ok": False, "error": "XHS_GENERAL_URL 为空", "meta": meta}
        max_pages = int(params.get("max_pages", 10))
        summary = fetch_xhs_all(url, str(key).strip(), params, max_pages)
        ok = summary["last_error"] is None and not summary["insufficient_balance"]
        if summary["insufficient_balance"]:
            ok = False
        return {"ok": ok, "data": summary, "meta": meta}

    return {
        "ok": False,
        "error": f"unsupported action: {action!r}；支持: xhs_search_page, xhs_search_all",
        "meta": meta,
    }
