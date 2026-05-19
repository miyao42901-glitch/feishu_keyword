"""公众号 Worker 任务入口（复用视频号逻辑，mode=2 + BusinessType + Sub_search_type 映射）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from mp_worker.spider import MpSpider

from http_api.constants import SHIPINHAO_GENERAL_URL
from social_platform.search_api_params import merge_search_all_api_params_into_body
from social_platform.services.search_persist import (
    persist_search_all_page_if_async,
    search_all_async_ctx,
)
from social_platform.utils.coercion import as_third_party_str
from social_platform.utils.search_fetch_all import (
    clamp_fetch_count_cap,
    coerce_optional_list_sort_type,
    fetch_offset_cookies_search_all,
    parse_optional_datetime,
    resolve_search_all_date_bounds,
)
from social_platform.utils.worker_runtime import service_url, worker_meta

WORKER_NAME = "mp_worker"
WORKER_VERSION = "1.0.0"

# 对外 sort_type (0/1/2) → Sub_search_type
MP_SORT_TYPE_MAP: dict[int, int] = {0: 0, 1: 4, 2: 2}


def _mp_search_json_body(params: dict[str, Any]) -> dict[str, Any]:
    """公众号搜索 body 构造（mode=2, BusinessType=2, sort 映射为 Sub_search_type）。"""
    st = params.get("sort_type")
    try:
        st_int = int(st) if st is not None else 0
    except (TypeError, ValueError):
        st_int = 0
    mapped_sub = MP_SORT_TYPE_MAP.get(st_int, 0)

    page_val = params.get("page") or params.get("currentPage", 1)
    try:
        page_val = max(1, int(page_val))
    except (TypeError, ValueError):
        page_val = 1

    body: dict[str, Any] = {
        "mode": 2,
        "BusinessType": 2,
        "keyword": str(params.get("keyword") or ""),
        "Sub_search_type": mapped_sub,
        "note_time": params.get("note_time", 0),
        "currentPage": page_val,
        "offset": params.get("offset", 0),
        "cookies_buffer": params.get("cookies_buffer", ""),
        "exclude_words": as_third_party_str(params.get("exclude_words")),
    }
    return {k: v for k, v in body.items() if v != "" or k in ("keyword", "offset")}


def _mp_search_json_body_search_all(params: dict[str, Any]) -> dict[str, Any]:
    return merge_search_all_api_params_into_body(_mp_search_json_body(params), params)


def call_mp_api(api_url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:
    return MpSpider(api_url).run(body, headers={"X-API-Key": key.strip()})


def fetch_mp_all(
    api_url: str,
    key: str,
    params: dict[str, Any],
    max_pages: Optional[int] = None,
    *,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    list_sort_type: Optional[int] = None,
    fetch_count_cap: int = 100,
    after_each_page: Optional[Callable[[list[dict[str, Any]]], None]] = None,
) -> dict[str, Any]:
    return fetch_offset_cookies_search_all(
        api_url,
        key,
        params,
        body_builder=_mp_search_json_body_search_all,
        api_call=call_mp_api,
        max_pages=max_pages,
        start_date=start_date,
        end_date=end_date,
        list_sort_type=list_sort_type,
        fetch_count_cap=fetch_count_cap,
        after_each_page=after_each_page,
        log_platform="mp",
    )


def _optional_max_pages(params: dict[str, Any]) -> Optional[int]:
    if "max_pages" not in params:
        return None
    v = params.get("max_pages")
    if v is None:
        return None
    if isinstance(v, str) and not str(v).strip():
        return None
    return int(v)


def execute_mp_search_all(
    params: dict[str, Any],
    *,
    sync_page_save: Optional[Callable[[list[dict[str, Any]]], None]] = None,
) -> dict[str, Any]:
    """供 HTTP 同步与 Celery 共用；可选每页落库。"""
    meta = worker_meta(WORKER_NAME, WORKER_VERSION)
    key, keyword = params.get("key"), params.get("keyword")
    if not key or not keyword:
        return {"ok": False, "error": "missing key or keyword", "meta": meta}
    url = service_url(SHIPINHAO_GENERAL_URL)
    if not url:
        return {"ok": False, "error": "SHIPINHAO_GENERAL_URL 为空", "meta": meta}
    max_pages = _optional_max_pages(params)
    list_st = coerce_optional_list_sort_type(params)
    fetch_n = clamp_fetch_count_cap(params)
    start_d = parse_optional_datetime(params.get("start_date"))
    end_d = parse_optional_datetime(params.get("end_date"))
    start_d, end_d = resolve_search_all_date_bounds(
        params, list_sort_type=list_st, start_d=start_d, end_d=end_d
    )
    use_after = sync_page_save is not None or search_all_async_ctx.get() is not None

    def after_chunk(chunk: list[dict[str, Any]]) -> None:
        if not chunk:
            return
        if sync_page_save is not None:
            sync_page_save(chunk)
        persist_search_all_page_if_async(chunk)

    summary = fetch_mp_all(
        url,
        str(key).strip(),
        params,
        max_pages,
        start_date=start_d,
        end_date=end_d,
        list_sort_type=list_st,
        fetch_count_cap=fetch_n,
        after_each_page=after_chunk if use_after else None,
    )
    if use_after:
        summary["_incremental_persist"] = True
    ok = summary["last_error"] is None and not summary["insufficient_balance"]
    if summary["insufficient_balance"]:
        ok = False
    return {"ok": ok, "data": summary, "meta": meta}


def run_task(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    params = payload.get("params") or {}
    meta = worker_meta(WORKER_NAME, WORKER_VERSION)

    if action in ("mp_search_page", "mp-search-page"):
        key, keyword = params.get("key"), params.get("keyword")
        if not key or not keyword:
            return {"ok": False, "error": "missing key or keyword", "meta": meta}
        url = service_url(SHIPINHAO_GENERAL_URL)
        if not url:
            return {"ok": False, "error": "SHIPINHAO_GENERAL_URL 为空", "meta": meta}
        raw = call_mp_api(url, str(key).strip(), _mp_search_json_body(params))
        ok = not raw.get("insufficient_balance") and raw.get("error") is None
        return {"ok": ok, "data": raw, "meta": meta}

    if action in ("mp_search_all", "mp-search-all"):
        return execute_mp_search_all(params)

    return {
        "ok": False,
        "error": f"unsupported action: {action!r}；支持: mp_search_page, mp_search_all",
        "meta": meta,
    }
