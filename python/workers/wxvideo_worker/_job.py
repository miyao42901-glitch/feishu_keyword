"""微信视频号（视频号搜索）Worker 任务入口。"""



from __future__ import annotations



from datetime import datetime

from typing import Any, Callable, Optional



from wxvideo_worker.spider import WxVideoSpider



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



WORKER_NAME = "wxvideo_worker"

WORKER_VERSION = "1.0.0"



# 对外 sort_type (0综合/1最新/2最热) → 后端 sort_type

WX_SORT_TYPE_MAP: dict[int, int] = {0: 0, 1: 2, 2: 1}



# 对外 note_time (0/1/7/180) → 后端 publish_time_type

WX_NOTE_TIME_MAP: dict[int, int] = {0: 0, 1: 1, 7: 2, 180: 3}





def _wx_sousou_json_body(params: dict[str, Any]) -> dict[str, Any]:

    """视频号 /wx/sousou search body 构造（含 sort_type 映射）。"""

    st = params.get("sort_type")

    try:

        st_int = int(st) if st is not None else 0

    except (TypeError, ValueError):

        st_int = 0

    mapped_sort = WX_SORT_TYPE_MAP.get(st_int, 0)



    nt = params.get("note_time")

    try:

        nt_int = int(nt) if nt is not None else 0

    except (TypeError, ValueError):

        nt_int = 0

    mapped_note_time = WX_NOTE_TIME_MAP.get(nt_int, 0)



    body: dict[str, Any] = {

        "mode": 1,

        "keyword": str(params.get("keyword") or ""),

        "search_type": 2,

        "publish_time_type": mapped_note_time,

        "sort_type": mapped_sort,

        "currentPage": params.get("page") or params.get("currentPage", 1),

        "offset": params.get("offset", 0),

        "cookies_buffer": params.get("cookies_buffer", ""),

        "exclude_words": as_third_party_str(params.get("exclude_words")),

    }

    return {k: v for k, v in body.items() if v != "" or k in ("keyword", "offset")}





def _wx_sousou_json_body_search_all(params: dict[str, Any]) -> dict[str, Any]:

    return merge_search_all_api_params_into_body(_wx_sousou_json_body(params), params)





def call_wxvideo_api(api_url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:

    return WxVideoSpider(api_url).run(body, headers={"X-API-Key": key.strip()})





def fetch_wxvideo_all(

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
    fetch_count_cap = clamp_fetch_count_cap(params)

    return fetch_offset_cookies_search_all(

        api_url,

        key,

        params,

        body_builder=_wx_sousou_json_body_search_all,

        api_call=call_wxvideo_api,

        max_pages=max_pages,

        start_date=start_date,

        end_date=end_date,

        list_sort_type=list_sort_type,

        fetch_count_cap=fetch_count_cap,

        after_each_page=after_each_page,
        log_platform="wxvideo",

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





def execute_wxvideo_search_all(

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



    summary = fetch_wxvideo_all(

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





def run_task(payload: dict[str, Any]) -> dict[str, Any]:

    action = payload.get("action")

    params = payload.get("params") or {}

    meta = worker_meta(WORKER_NAME, WORKER_VERSION)



    if action in ("wxvideo_search_page", "wx_sousou_search_page"):

        key, keyword = params.get("key"), params.get("keyword")

        if not key or not keyword:

            return {"ok": False, "error": "missing key or keyword", "meta": meta}

        url = service_url(SHIPINHAO_GENERAL_URL)

        if not url:

            return {"ok": False, "error": "SHIPINHAO_GENERAL_URL 为空", "meta": meta}

        raw = call_wxvideo_api(url, str(key).strip(), _wx_sousou_json_body(params))

        ok = not raw.get("insufficient_balance") and raw.get("error") is None

        return {"ok": ok, "data": raw, "meta": meta}



    if action in ("wxvideo_search_all", "wx_sousou_search_all"):

        return execute_wxvideo_search_all(params)



    return {

        "ok": False,

        "error": f"unsupported action: {action!r}；支持: wxvideo_search_page, wxvideo_search_all",

        "meta": meta,

    }

