"""
多页搜索拉取：支持「仅 max_pages」与「按发布时间窗口」两种模式。

.. note::
    第三方大加拉类 API 可能对检索时间跨度有额外限制（例如最多 30 天），
    以实际接口文档为准；本模块仅在客户端按 ``publish_time`` 过滤，不替代上游配额。

列表顺序假设为 **发布时间降序**（新 → 旧）。若上游为升序，「遇早于 start_date 即停」的逻辑需另行调整。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time as dt_time
from typing import Any, Callable, Optional

# 仅日期窗口模式且未传 max_pages 时，防止死循环的页数上限（可调大/小）
DEFAULT_SAFETY_MAX_PAGES = 500


def parse_optional_datetime(value: Any) -> Optional[datetime]:
    """从 HTTP/JSON 参数解析 ``datetime``；支持 ISO 字符串（含 ``Z``）。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        # 视为毫秒时间戳
        ms = int(value)
        if ms > 1e12:
            return datetime.utcfromtimestamp(ms / 1000.0)
        return datetime.utcfromtimestamp(float(ms))
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def yesterday_midnight_local() -> datetime:
    """本地日历「昨天 00:00:00」（naive）。"""
    now = datetime.now()
    y = (now.date() - timedelta(days=1))
    return datetime.combine(y, dt_time.min)


def to_epoch_ms(dt: datetime) -> int:
    if dt.tzinfo is not None:
        return int(dt.timestamp() * 1000)
    return int(dt.replace(tzinfo=None).timestamp() * 1000)


def publish_time_ms_from_record(rec: Any) -> Optional[int]:
    """解析单条记录中的发布时间（毫秒），与各 Worker Parser 输出字段一致。"""
    if not isinstance(rec, dict):
        return None
    v = rec.get("publish_time")
    if v is None:
        return None
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n


def crawled_record_id(rec: dict[str, Any]) -> Optional[str]:
    """与 ``result_store_service._resolve_post_id`` 对齐的爬取结果主键（用于多页去重）。"""
    for key in ("note_id", "aweme_id", "post_id", "item_id"):
        v = rec.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def unique_new_records(
    chunk: list[dict[str, Any]],
    seen_ids: set[str],
    *,
    limit: Optional[int] = None,
) -> list[dict[str, Any]]:
    """
    去掉本任务已见过的 ``note_id`` / ``aweme_id``；``limit`` 为本次最多追加条数。
    无业务主键的记录仍会保留（无法跨页去重）。
    """
    out: list[dict[str, Any]] = []
    for rec in chunk:
        if not isinstance(rec, dict):
            continue
        pid = crawled_record_id(rec)
        if pid is not None:
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
        out.append(rec)
        if limit is not None and len(out) >= limit:
            break
    return out


@dataclass
class FetchAllMode:
    """内部使用的模式描述。"""

    use_date_window: bool
    start_ms: int
    end_ms: int
    page_cap: Optional[int]
    """有上界时：最多请求的页数（日期模式为防无限；纯页数模式即 max_pages）。"""
    safety_max_pages: int
    """日期模式且未显式传 max_pages 时使用的安全页上限。"""


def resolve_fetch_all_mode(
    *,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    max_pages: Optional[int],
    list_sort_type: Optional[int] = None,
) -> FetchAllMode:
    """
    - ``list_sort_type in (0, 1)`` 且无显式日期且无 ``max_pages``：不按时间窗过滤（客户端不按 ``time_range`` 截窗）。
    - ``list_sort_type is None`` 且无日期且无 ``max_pages``：**兼容旧行为**「昨天 00:00～当前」。
    - ``list_sort_type == 2`` 且无显式日期：由上层用 ``time_range`` 解析出起止时间后再进入本函数（见 ``resolve_search_all_date_bounds``）。
    - 有显式 ``start_date`` / ``end_date``：时间窗模式（与 ``list_sort_type`` 无关）。
    - 仅有 ``max_pages``：纯页数上限模式。
    """
    has_dates = start_date is not None or end_date is not None
    has_max = max_pages is not None

    if not has_dates and not has_max and list_sort_type in (0, 1):
        return FetchAllMode(
            use_date_window=False,
            start_ms=0,
            end_ms=2**63 - 1,
            page_cap=None,
            safety_max_pages=DEFAULT_SAFETY_MAX_PAGES,
        )

    if not has_dates and not has_max and list_sort_type is None:
        now = datetime.now()
        sd = yesterday_midnight_local()
        ed = now
        return FetchAllMode(
            use_date_window=True,
            start_ms=to_epoch_ms(sd),
            end_ms=to_epoch_ms(ed),
            page_cap=None,
            safety_max_pages=DEFAULT_SAFETY_MAX_PAGES,
        )

    if not has_dates and has_max:
        # 纯页数：时间窗口占位，不使用
        return FetchAllMode(
            use_date_window=False,
            start_ms=0,
            end_ms=2**63 - 1,
            page_cap=max(1, int(max_pages)),
            safety_max_pages=max(1, int(max_pages)),
        )

    # 日期模式（显式或部分显式）
    now = datetime.now()
    sd = start_date or yesterday_midnight_local()
    ed = end_date or now
    start_ms = to_epoch_ms(sd)
    end_ms = to_epoch_ms(ed)
    if start_ms > end_ms:
        start_ms, end_ms = end_ms, start_ms

    cap: Optional[int] = None
    safety = DEFAULT_SAFETY_MAX_PAGES
    if max_pages is not None:
        cap = max(1, int(max_pages))
        safety = cap

    return FetchAllMode(
        use_date_window=True,
        start_ms=start_ms,
        end_ms=end_ms,
        page_cap=cap,
        safety_max_pages=safety,
    )


def filter_records_by_publish_window(
    records: list[Any],
    start_ms: int,
    end_ms: int,
) -> tuple[list[dict[str, Any]], bool]:
    """
    按发布时间窗口过滤；假设 **新 → 旧** 排序。

    :return: (保留的记录, 是否应停止继续请求下一页——因已遇到早于 start 的条目)
    """
    kept: list[dict[str, Any]] = []
    stop_fetching = False
    for rec in records:
        if not isinstance(rec, dict):
            continue
        ts = publish_time_ms_from_record(rec)
        if ts is None:
            kept.append(rec)
            continue
        if ts > end_ms:
            continue
        if ts < start_ms:
            stop_fetching = True
            break
        kept.append(rec)
    return kept, stop_fetching


def build_fetch_all_meta(
    *,
    mode: FetchAllMode,
    start_date_effective: Optional[datetime],
    end_date_effective: Optional[datetime],
    truncated_by_max_pages: bool,
    stopped_before_start_date: bool,
    pages_fetched: int,
) -> dict[str, Any]:
    def _iso(d: Optional[datetime]) -> Optional[str]:
        if d is None:
            return None
        return d.replace(microsecond=0).isoformat()

    return {
        "use_date_window": mode.use_date_window,
        "start_date_effective": _iso(start_date_effective),
        "end_date_effective": _iso(end_date_effective),
        "start_ms_effective": mode.start_ms if mode.use_date_window else None,
        "end_ms_effective": mode.end_ms if mode.use_date_window else None,
        "truncated_by_max_pages": truncated_by_max_pages,
        "stopped_before_start_date": stopped_before_start_date,
        "pages_fetched": pages_fetched,
        "safety_max_pages": mode.safety_max_pages,
    }


def coerce_optional_list_sort_type(params: dict[str, Any]) -> Optional[int]:
    """请求体未带 ``sort_type`` 时返回 ``None``（兼容旧任务）；否则为 ``0`` / ``1`` / ``2``。"""
    if "sort_type" not in params:
        return None
    v = params.get("sort_type")
    if v is None or (isinstance(v, str) and not str(v).strip()):
        return None
    n = int(v)
    return n


def clamp_fetch_count_cap(params: dict[str, Any], *, default: int = 100) -> int:
    """与 Model 一致：1～500；缺省 ``default``。"""
    raw = params.get("fetch_count", default)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = default
    return max(1, min(500, n))


def resolve_search_all_date_bounds(
    params: dict[str, Any],
    *,
    list_sort_type: Optional[int],
    start_d: Optional[datetime],
    end_d: Optional[datetime],
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    显式 ``start_date`` / ``end_date`` 优先；否则当 ``list_sort_type == 2`` 时，
    用 ``time_range``（天）得到 ``[now - days, now]``。
    """
    if start_d is not None or end_d is not None:
        return start_d, end_d
    if list_sort_type == 2:
        end = datetime.now()
        try:
            tr = int(params.get("time_range") or 7)
        except (TypeError, ValueError):
            tr = 7
        tr = max(1, tr)
        start = end - timedelta(days=tr)
        return start, end
    return start_d, end_d


def fetch_douyin_search_all(
    api_url: str,
    key: str,
    params: dict[str, Any],
    *,
    body_builder: Callable[[dict[str, Any]], dict[str, Any]],
    api_call: Callable[[str, str, dict[str, Any]], dict[str, Any]],
    max_pages: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    list_sort_type: Optional[int] = None,
    fetch_count_cap: int = 100,
    after_each_page: Optional[Callable[[list[dict[str, Any]]], None]] = None,
) -> dict[str, Any]:
    """
    抖音多页拉取。

    **默认行为**（与产品需求一致）::

        若 ``start_date`` / ``end_date`` / ``max_pages`` 均未传入（或 max_pages 为 None）：
            使用「昨天本地 00:00:00」～「当前本地时间」作为时间窗，按页拉取直到
            遇到发布时间早于窗口下界或达到安全页数上限。

        若仅传入 ``max_pages``：按页数上限拉取，**不按**发布时间过滤（与旧版一致）。

        若传入时间窗：只保留 ``publish_time`` 落在 ``[start, end]`` 内的记录；可选 ``max_pages``
        限制最多请求页数，防止异常情况下死循环。

    ``list_sort_type``：``0`` / ``1`` 在无显式日期且无 ``max_pages`` 时不按时间窗过滤；
    ``2`` 配合 ``time_range`` 由调用方先解析日期边界；``None`` 兼容旧请求（「昨天～当前」）。
    ``fetch_count_cap``：采集条数上限，与时间窗或数据源耗尽任一先满足即停。
    """
    fetch_count_cap = max(1, min(500, int(fetch_count_cap)))
    mode = resolve_fetch_all_mode(
        start_date=start_date,
        end_date=end_date,
        max_pages=max_pages,
        list_sort_type=list_sort_type,
    )
    start_eff = (
        datetime.fromtimestamp(mode.start_ms / 1000.0)
        if mode.use_date_window
        else None
    )
    end_eff = (
        datetime.fromtimestamp(mode.end_ms / 1000.0)
        if mode.use_date_window
        else None
    )

    all_data: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    balance = 0.0
    body = body_builder(params)
    insufficient_balance = False
    last_error = None
    stopped_before_start = False
    pages = 0
    duplicate_pages_in_row = 0

    page_limit = mode.page_cap if mode.page_cap is not None else mode.safety_max_pages

    while pages < page_limit:
        remaining = fetch_count_cap - len(all_data)
        if remaining <= 0:
            break
        result = api_call(api_url, key, body)
        if result.get("insufficient_balance"):
            insufficient_balance = True
            break
        if result.get("error"):
            last_error = result["error"]
            break
        raw_data = result.get("data") or []
        if not isinstance(raw_data, list):
            raw_data = []

        balance = result.get("balance", balance)

        if mode.use_date_window:
            chunk, stop = filter_records_by_publish_window(
                raw_data, mode.start_ms, mode.end_ms
            )
        else:
            chunk = [r for r in raw_data if isinstance(r, dict)]
            stop = False

        window_stop = stop
        new_chunk = unique_new_records(chunk, seen_ids, limit=remaining)
        all_data.extend(new_chunk)
        pages += 1
        if after_each_page is not None and new_chunk:
            after_each_page(list(new_chunk))
        if len(all_data) >= fetch_count_cap:
            break
        if window_stop:
            stopped_before_start = True
            break

        if not raw_data:
            break
        if not new_chunk:
            duplicate_pages_in_row += 1
            if duplicate_pages_in_row >= 5:
                break
        else:
            duplicate_pages_in_row = 0

        if len(raw_data) < 5 and len(all_data) < fetch_count_cap:
            break

        body = dict(body)
        body["cursor"] = str(result.get("next_cursor", ""))
        body["log_id"] = str(result.get("next_logid", ""))

    truncated = (
        pages >= page_limit
        and not stopped_before_start
        and last_error is None
        and not insufficient_balance
    )

    meta = build_fetch_all_meta(
        mode=mode,
        start_date_effective=start_eff,
        end_date_effective=end_eff,
        truncated_by_max_pages=truncated,
        stopped_before_start_date=stopped_before_start,
        pages_fetched=pages,
    )
    meta["fetch_count_cap"] = fetch_count_cap
    meta["records_returned"] = len(all_data)

    return {
        "records": all_data,
        "balance": balance,
        "insufficient_balance": insufficient_balance,
        "last_error": last_error,
        "meta": meta,
    }


def fetch_xhs_search_all(
    api_url: str,
    key: str,
    params: dict[str, Any],
    *,
    body_builder: Callable[[dict[str, Any]], dict[str, Any]],
    api_call: Callable[[str, str, dict[str, Any]], dict[str, Any]],
    max_pages: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    list_sort_type: Optional[int] = None,
    fetch_count_cap: int = 100,
    after_each_page: Optional[Callable[[list[dict[str, Any]]], None]] = None,
) -> dict[str, Any]:
    """
    小红书多页拉取（页码式 cursor）。行为说明同 :func:`fetch_douyin_search_all`。
    """
    fetch_count_cap = max(1, min(500, int(fetch_count_cap)))
    mode = resolve_fetch_all_mode(
        start_date=start_date,
        end_date=end_date,
        max_pages=max_pages,
        list_sort_type=list_sort_type,
    )
    start_eff = (
        datetime.fromtimestamp(mode.start_ms / 1000.0)
        if mode.use_date_window
        else None
    )
    end_eff = (
        datetime.fromtimestamp(mode.end_ms / 1000.0)
        if mode.use_date_window
        else None
    )

    base = body_builder(params)
    try:
        start = max(1, int(base.get("page") or base.get("cursor") or 1))
    except (TypeError, ValueError):
        start = 1

    all_data: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    balance = 0.0
    insufficient_balance = False
    last_error = None
    stopped_before_start = False
    pages = 0
    duplicate_pages_in_row = 0

    page_limit = mode.page_cap if mode.page_cap is not None else mode.safety_max_pages

    while pages < page_limit:
        remaining = fetch_count_cap - len(all_data)
        if remaining <= 0:
            break
        body = dict(body_builder(params))
        body["page"] = start + pages
        body.pop("cursor", None)
        result = api_call(api_url, key, body)
        if result.get("insufficient_balance"):
            insufficient_balance = True
            break
        if result.get("error"):
            last_error = result["error"]
            break
        raw_data = result.get("data") or []
        if not isinstance(raw_data, list):
            raw_data = []

        balance = result.get("balance", balance)

        if mode.use_date_window:
            chunk, stop = filter_records_by_publish_window(
                raw_data, mode.start_ms, mode.end_ms
            )
        else:
            chunk = [r for r in raw_data if isinstance(r, dict)]
            stop = False

        window_stop = stop
        new_chunk = unique_new_records(chunk, seen_ids, limit=remaining)
        all_data.extend(new_chunk)
        pages += 1
        if after_each_page is not None and new_chunk:
            after_each_page(list(new_chunk))
        if len(all_data) >= fetch_count_cap:
            break
        if window_stop:
            stopped_before_start = True
            break

        if not raw_data:
            break
        if not new_chunk:
            duplicate_pages_in_row += 1
            if duplicate_pages_in_row >= 5:
                break
        else:
            duplicate_pages_in_row = 0

    truncated = (
        pages >= page_limit
        and not stopped_before_start
        and last_error is None
        and not insufficient_balance
    )

    meta = build_fetch_all_meta(
        mode=mode,
        start_date_effective=start_eff,
        end_date_effective=end_eff,
        truncated_by_max_pages=truncated,
        stopped_before_start_date=stopped_before_start,
        pages_fetched=pages,
    )
    meta["fetch_count_cap"] = fetch_count_cap
    meta["records_returned"] = len(all_data)

    return {
        "records": all_data,
        "balance": balance,
        "insufficient_balance": insufficient_balance,
        "last_error": last_error,
        "meta": meta,
    }
