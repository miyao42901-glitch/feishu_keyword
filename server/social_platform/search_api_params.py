"""
search-all 等：第三方检索 API 的占位参数映射。

请按实际大加拉 / 平台接口字段名修改 ``build_search_all_api_params`` 的返回值，
并在各 Worker 的 ``_third_party_json_body`` 中合并进最终 POST body。
"""

from __future__ import annotations

from typing import Any, Optional


def build_search_all_api_params(
    *,
    fetch_count: int,
    time_range: int,
    sort_type: int,
) -> dict[str, Any]:
    """
    构建第三方 API 请求扩展字段（占位）。

    - 仅 ``sort_type == 2`` 时把 ``time_range``（天）写入 ``days``；其它取值不传 ``days``。
    - ``sort_type == 0``：默认/综合类占位（请按实际接口改 ``sort`` 取值）。
    - ``1``：相关性；``2``：按时间（与 ``time_range`` 联用）。
    """
    if sort_type == 2:
        sort_val = "time"
    elif sort_type == 1:
        sort_val = "relevance"
    else:
        sort_val = "default"
    api_params: dict[str, Any] = {
        "count": fetch_count,
        "sort": sort_val,
    }
    if sort_type == 2:
        api_params["days"] = time_range
    return api_params


def merge_search_all_api_params_into_body(
    body: dict[str, Any], params: dict[str, Any]
) -> dict[str, Any]:
    """将占位映射合并进下游 body；仅合并调用方显式传入的 search-all 控制字段。"""
    raw_fc = params.get("fetch_count")
    raw_tr = params.get("time_range")
    raw_st = params.get("sort_type")
    if raw_fc is None and raw_tr is None and raw_st is None:
        return dict(body)
    fetch_count = int(raw_fc) if raw_fc is not None else 100
    time_range = int(raw_tr) if raw_tr is not None else 7
    if raw_st is None or (isinstance(raw_st, str) and not str(raw_st).strip()):
        sort_type = 1
    else:
        sort_type = int(raw_st)
    extra = build_search_all_api_params(
        fetch_count=fetch_count,
        time_range=time_range,
        sort_type=sort_type,
    )
    out = dict(body)
    if raw_fc is not None:
        out["count"] = extra["count"]
    if raw_st is not None and str(raw_st).strip() != "":
        out["sort"] = extra["sort"]
        if sort_type == 2 and raw_tr is not None:
            out["days"] = extra["days"]
    return out
