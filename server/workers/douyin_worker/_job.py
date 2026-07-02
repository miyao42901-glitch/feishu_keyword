"""抖音 Worker 任务入口。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from douyin_worker.spider import DouyinSpider

from http_api.constants import DOUYIN_GENERAL_URL
from social_platform.search_api_params import merge_search_all_api_params_into_body
from social_platform.services.search_persist import (
    persist_search_all_page_if_async,
    search_all_async_ctx,
)
from social_platform.utils.coercion import as_third_party_str, optional_body_str
from social_platform.utils.search_fetch_all import (
    clamp_fetch_count_cap,
    coerce_optional_list_sort_type,
    fetch_douyin_search_all,
    parse_optional_datetime,
    resolve_search_all_date_bounds,
)
from social_platform.utils.worker_runtime import (
    API_KEY_HEADER,
    resolved_service_url,
    worker_meta,
)

WORKER_NAME = "douyin_worker"
WORKER_VERSION = "1.0.0"


def _douyin_json_body(
    params: dict[str, Any], *, include_cursor_from_page: bool
) -> dict[str, Any]:
    """抖音搜索 POST body；未传字段不写入。"""
    body: dict[str, Any] = {"keyword": str(params.get("keyword") or "")}
    cursor = optional_body_str(params, "cursor")
    if include_cursor_from_page and not cursor:
        cursor = optional_body_str(params, "page")
    if cursor:
        body["cursor"] = cursor
    log_id = optional_body_str(params, "log_id", "logid")
    if log_id:
        body["log_id"] = log_id
    sort_type = optional_body_str(params, "sort_type")
    if sort_type:
        body["sort_type"] = sort_type
    for key in ("publish_time", "filter_duration", "content_type"):
        value = optional_body_str(params, key)
        if value:
            body[key] = value
    exclude_words = as_third_party_str(params.get("exclude_words")).strip()
    if exclude_words:
        body["exclude_words"] = exclude_words
    return body


def _third_party_json_body(params: dict[str, Any]) -> dict[str, Any]:
    """抖音 search-all 等多页场景（cursor 翻页）。"""
    return _douyin_json_body(params, include_cursor_from_page=True)


def _douyin_page_json_body(params: dict[str, Any]) -> dict[str, Any]:
    """抖音单页搜索 POST body。"""
    return _douyin_json_body(params, include_cursor_from_page=False)


def _third_party_json_body_search_all(params: dict[str, Any]) -> dict[str, Any]:
    return merge_search_all_api_params_into_body(_third_party_json_body(params), params)


def call_douyin_api(api_url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:
    return DouyinSpider(api_url).run(body, headers={API_KEY_HEADER: key.strip()})


def fetch_douyin_all(
    api_url: str,
    key: str,
    params: dict[str, Any],
    max_pages: Optional[int] = None,
    *,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    list_sort_type: Optional[int] = None,
    after_each_page: Optional[Callable[[list[dict[str, Any]]], Optional[int]]] = None,
) -> dict[str, Any]:
    """
    多页拉取抖音搜索结果。

    默认与参数语义见 :func:`social_platform.utils.search_fetch_all.fetch_douyin_search_all`。
    若上游对检索时间跨度有限制（如最多 30 天），请以接口文档为准；此处仅按解析结果过滤。
    """
    fetch_count_cap = clamp_fetch_count_cap(params)
    return fetch_douyin_search_all(
        api_url,
        key,
        params,
        body_builder=_third_party_json_body_search_all,
        api_call=call_douyin_api,
        max_pages=max_pages,
        start_date=start_date,
        end_date=end_date,
        list_sort_type=list_sort_type,
        fetch_count_cap=fetch_count_cap,
        after_each_page=after_each_page,
    )


def execute_douyin_search_all(
    params: dict[str, Any],
    *,
    sync_page_save: Optional[Callable[[list[dict[str, Any]]], None]] = None,
) -> dict[str, Any]:
    """供 HTTP 同步与 ``run_task`` 共用；可选 ``sync_page_save`` 在每页过滤后落库。"""
    meta = worker_meta(WORKER_NAME, WORKER_VERSION)
    key, keyword = params.get("key"), params.get("keyword")
    if not key or not keyword:
        return {"ok": False, "error": "missing key or keyword", "meta": meta}
    url = resolved_service_url("DOUYIN_GENERAL_URL", DOUYIN_GENERAL_URL)
    if not url:
        return {"ok": False, "error": "DOUYIN_GENERAL_URL 为空", "meta": meta}
    max_pages = _optional_max_pages(params)
    list_st = coerce_optional_list_sort_type(params)
    # 统一使用 time 参数（日期+时间）；兼容历史 start_date / end_date。
    start_d = parse_optional_datetime(params.get("start_time") or params.get("start_date"))
    end_d = parse_optional_datetime(params.get("end_time") or params.get("end_date"))
    start_d, end_d = resolve_search_all_date_bounds(
        params, list_sort_type=list_st, start_d=start_d, end_d=end_d
    )
    use_after = sync_page_save is not None or search_all_async_ctx.get() is not None

    def after_chunk(chunk: list[dict[str, Any]]) -> Optional[int]:
        if not chunk:
            return 0
        has_async_ctx = search_all_async_ctx.get() is not None
        inserted_count = 0
        if sync_page_save is not None:
            sync_page_save(chunk)
            if not has_async_ctx:
                inserted_count = len(chunk)
        async_inserted = persist_search_all_page_if_async(chunk)
        if has_async_ctx:
            return int(async_inserted)
        return inserted_count

    summary = fetch_douyin_all(
        url,
        str(key).strip(),
        params,
        max_pages,
        start_date=start_d,
        end_date=end_d,
        list_sort_type=list_st,
        after_each_page=after_chunk if use_after else None,
    )
    if use_after:
        summary["_incremental_persist"] = True
    ok = summary["last_error"] is None and not summary["insufficient_balance"]
    if summary["insufficient_balance"]:
        ok = False
    return {"ok": ok, "data": summary, "meta": meta}


def _optional_max_pages(params: dict[str, Any]) -> Optional[int]:
    if "max_pages" not in params:
        return None
    v = params.get("max_pages")
    if v is None:
        return None
    if isinstance(v, str) and not str(v).strip():
        return None
    return int(v)


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
        return execute_douyin_search_all(params)

    return {
        "ok": False,
        "error": f"unsupported action: {action!r}；支持: douyin_search_page, douyin_search_all",
        "meta": meta,
    }
