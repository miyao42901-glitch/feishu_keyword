"""小红书 Worker 任务入口。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from http_api.constants import XHS_GENERAL_URL
from social_platform.search_api_params import merge_search_all_api_params_into_body
from social_platform.services.search_persist import (
    persist_search_all_page_if_async,
    search_all_async_ctx,
)
from social_platform.utils.coercion import as_third_party_str
from social_platform.utils.search_fetch_all import (
    clamp_fetch_count_cap,
    coerce_optional_list_sort_type,
    fetch_xhs_search_all,
    parse_optional_datetime,
    resolve_search_all_date_bounds,
)
from social_platform.utils.worker_runtime import API_KEY_HEADER, resolved_service_url, worker_meta
from xhs_worker.spider import XhsSpider

WORKER_NAME = "xhs_worker"
WORKER_VERSION = "1.0.0"

# 对外 sort_type（0/1/2）→ YDDM sort
XHS_SORT_TYPE_TO_YDDM: dict[str, str] = {
    "0": "general",
    "1": "popularity_descending",
    "2": "time_descending",
}

# 对外 note_time（0/1/7/180）→ YDDM note_time（空串=不限）
XHS_NOTE_TIME_TO_YDDM: dict[str, str] = {
    "0": "",
    "1": "day",
    "7": "week",
    "180": "halfyear",
}

# 对外 content_type → YDDM note_type（空串=不限）
XHS_CONTENT_TYPE_TO_NOTE_TYPE: dict[str, str] = {
    "2": "video",
    "1": "note",
    "": "",
    "0": "",
}


def _normalize_xhs_sort_type(params: dict[str, Any]) -> str:
    st = params.get("sort_type")
    if st is None or (isinstance(st, str) and not str(st).strip()):
        return "0"
    return str(st).strip()


def _normalize_xhs_note_time(params: dict[str, Any]) -> str:
    nt = params.get("note_time")
    if nt is None or (isinstance(nt, str) and not str(nt).strip()):
        nt = params.get("publish_time")
    if nt is None or (isinstance(nt, str) and not str(nt).strip()):
        return "0"
    return str(nt).strip()


def _normalize_xhs_content_type(params: dict[str, Any]) -> str:
    ct = as_third_party_str(params.get("content_type"))
    return ct.strip().lower()


def map_xhs_params_to_yddm_body(
    params: dict[str, Any],
    *,
    page: Optional[int] = None,
) -> dict[str, Any]:
    """
    将对外检索参数字典映射为 YDDM 小红书搜索 POST body。

    示例入参::

        {"keyword": "穿搭博主", "page": 1, "sort_type": "2",
         "content_type": "video", "note_time": "7", "exclude_words": "测试"}

    映射为::

        {"keyword": "穿搭博主", "page": 1, "sort": "time_descending",
         "note_type": "video", "note_time": "week", "exclude_words": "测试"}
    """
    if page is None:
        try:
            page_n = max(1, int(params.get("page") or 1))
        except (TypeError, ValueError):
            page_n = 1
    else:
        page_n = max(1, int(page))

    sort_key = _normalize_xhs_sort_type(params)
    note_time_key = _normalize_xhs_note_time(params)
    content_key = _normalize_xhs_content_type(params)

    body: dict[str, Any] = {
        "keyword": str(params.get("keyword") or ""),
        "page": page_n,
        "sort": XHS_SORT_TYPE_TO_YDDM.get(sort_key, "general"),
        "note_type": XHS_CONTENT_TYPE_TO_NOTE_TYPE.get(content_key, ""),
        "note_time": XHS_NOTE_TIME_TO_YDDM.get(note_time_key, ""),
    }
    exclude_words = as_third_party_str(params.get("exclude_words"))
    if exclude_words:
        body["exclude_words"] = exclude_words
    return body


def _third_party_json_body(params: dict[str, Any]) -> dict[str, Any]:
    """小红书 search-all：由 fetch 循环按页覆盖 ``page``。"""
    try:
        page = max(1, int(params.get("page") or params.get("cursor") or 1))
    except (TypeError, ValueError):
        page = 1
    return map_xhs_params_to_yddm_body(params, page=page)


def _third_party_json_body_search_all(params: dict[str, Any]) -> dict[str, Any]:
    return merge_search_all_api_params_into_body(_third_party_json_body(params), params)


def _xhs_page_json_body(params: dict[str, Any]) -> dict[str, Any]:
    """小红书单页搜索 POST body（YDDM 字段）。"""
    return map_xhs_params_to_yddm_body(params)


def _xhs_body_for_page(params: dict[str, Any]) -> dict[str, Any]:
    return _xhs_page_json_body(params)


def call_xhs_api(api_url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:
    return XhsSpider(api_url).run(body, headers={API_KEY_HEADER: key.strip()})


def fetch_xhs_all(
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
    """
    多页拉取小红书搜索结果。

    默认与参数语义见 :func:`social_platform.utils.search_fetch_all.fetch_xhs_search_all`。
    底层 API 若支持 ``publish_time`` / ``note_time`` 等筛选项，仍可通过 ``params`` 传入；
    时间窗过滤以解析后的 ``publish_time``（毫秒）在客户端完成。
    """
    return fetch_xhs_search_all(
        api_url,
        key,
        params,
        body_builder=_third_party_json_body_search_all,
        api_call=call_xhs_api,
        max_pages=max_pages,
        start_date=start_date,
        end_date=end_date,
        list_sort_type=list_sort_type,
        fetch_count_cap=fetch_count_cap,
        after_each_page=after_each_page,
    )


def execute_xhs_search_all(
    params: dict[str, Any],
    *,
    sync_page_save: Optional[Callable[[list[dict[str, Any]]], None]] = None,
) -> dict[str, Any]:
    """供 HTTP 同步与 ``run_task`` 共用；可选 ``sync_page_save`` 在每页过滤后落库。"""
    meta = worker_meta(WORKER_NAME, WORKER_VERSION)
    key, keyword = params.get("key"), params.get("keyword")
    if not key or not keyword:
        return {"ok": False, "error": "missing key or keyword", "meta": meta}
    url = resolved_service_url("XHS_GENERAL_URL", XHS_GENERAL_URL)
    if not url:
        return {"ok": False, "error": "XHS_GENERAL_URL 为空", "meta": meta}
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

    summary = fetch_xhs_all(
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

    if action == "xhs_search_page":
        key, keyword = params.get("key"), params.get("keyword")
        if not key or not keyword:
            return {"ok": False, "error": "missing key or keyword", "meta": meta}
        url = resolved_service_url("XHS_GENERAL_URL", XHS_GENERAL_URL)
        if not url:
            return {"ok": False, "error": "XHS_GENERAL_URL 为空", "meta": meta}
        raw = call_xhs_api(url, str(key).strip(), _xhs_body_for_page(params))
        ok = not raw.get("insufficient_balance") and raw.get("error") is None
        return {"ok": ok, "data": raw, "meta": meta}

    if action == "xhs_search_all":
        return execute_xhs_search_all(params)

    return {
        "ok": False,
        "error": f"unsupported action: {action!r}；支持: xhs_search_page, xhs_search_all",
        "meta": meta,
    }
