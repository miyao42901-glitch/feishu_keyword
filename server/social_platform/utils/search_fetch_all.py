"""
多页搜索拉取：支持「仅 max_pages」与「按发布时间窗口」两种模式。

.. note::
    第三方大加拉类 API 可能对检索时间跨度有额外限制（例如最多 30 天），
    以实际接口文档为准；本模块仅在客户端按 ``publish_time`` 过滤，不替代上游配额。

列表顺序假设为 **发布时间降序**（新 → 旧）。若上游为升序，「遇早于 start_date 即停」的逻辑需另行调整。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta
from typing import Any, Callable, Optional

# 未启用严格止损时的兼容页数上限（与历史 DEFAULT_SAFETY_MAX_PAGES 一致）
LEGACY_SAFETY_MAX_PAGES = 500

# 明确可枚举的停止原因（写入 meta.stop_reason 与结构化日志）
STOP_FETCH_COUNT_REACHED = "fetch_count_reached"
STOP_MAX_PAGES_REACHED = "max_pages_reached"
STOP_MAX_RUN_SECONDS_REACHED = "max_run_seconds_reached"
STOP_NO_MORE_DATA = "no_more_data"
STOP_REPEATED_PAGE_TOKEN = "repeated_page_token"
STOP_EMPTY_PAGE = "empty_page"
STOP_DUPLICATE_PAGES_THRESHOLD = "duplicate_pages_threshold"
STOP_BEFORE_START_DATE = "before_start_date"
STOP_API_ERROR = "api_error"
STOP_INSUFFICIENT_BALANCE = "insufficient_balance"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchFetchGuardLimits:
    max_pages: int
    max_run_seconds: Optional[float]
    duplicate_page_threshold: int


def _guards_apply() -> bool:
    from config.settings import get_settings

    settings = get_settings()
    if not settings.async_search_guards_async_only:
        return True
    try:
        from social_platform.services.search_persist import search_all_async_ctx

        return search_all_async_ctx.get() is not None
    except Exception:
        return False


def _guard_limits() -> SearchFetchGuardLimits:
    from config.settings import get_settings

    settings = get_settings()
    if not _guards_apply():
        return SearchFetchGuardLimits(
            max_pages=LEGACY_SAFETY_MAX_PAGES,
            max_run_seconds=None,
            duplicate_page_threshold=max(
                1, int(settings.async_search_duplicate_page_threshold)
            ),
        )
    return SearchFetchGuardLimits(
        max_pages=max(1, int(settings.async_search_all_max_pages)),
        max_run_seconds=max(1.0, float(settings.async_search_all_max_run_seconds)),
        duplicate_page_threshold=max(
            1, int(settings.async_search_duplicate_page_threshold)
        ),
    )


def _configured_safety_max_pages() -> int:
    return _guard_limits().max_pages


def _get_task_id_for_log() -> Optional[int]:
    try:
        from social_platform.services.search_persist import search_all_async_ctx

        ctx = search_all_async_ctx.get()
        if ctx is None:
            return None
        return int(ctx.task_id)
    except Exception:
        return None


def _get_run_id_for_log() -> Optional[str]:
    try:
        from social_platform.services.search_persist import search_all_async_ctx

        ctx = search_all_async_ctx.get()
        if ctx is None:
            return None
        rid = str(getattr(ctx, "run_id", "") or "").strip()
        return rid or None
    except Exception:
        return None


def _log_fetch_structured(
    *,
    platform: str,
    page: int,
    pages_fetched: int,
    records_returned: int,
    fetch_count_cap: int,
    has_more: bool,
    duration_sec: float,
    stop_reason: Optional[str] = None,
) -> None:
    task_id = _get_task_id_for_log()
    run_id = _get_run_id_for_log()
    if stop_reason:
        logger.info(
            "search_fetch_all platform=%s task_id=%s run_id=%s page=%s pages_fetched=%s "
            "records_returned=%s fetch_count_cap=%s has_more=%s duration_sec=%.3f "
            "stop_reason=%s",
            platform,
            task_id if task_id is not None else "-",
            run_id or "-",
            page,
            pages_fetched,
            records_returned,
            fetch_count_cap,
            has_more,
            duration_sec,
            stop_reason,
        )
        return
    logger.info(
        "search_fetch_all platform=%s task_id=%s run_id=%s page=%s pages_fetched=%s "
        "records_returned=%s fetch_count_cap=%s has_more=%s duration_sec=%.3f",
        platform,
        task_id if task_id is not None else "-",
        run_id or "-",
        page,
        pages_fetched,
        records_returned,
        fetch_count_cap,
        has_more,
        duration_sec,
    )


def _log_search_fetch_all_stop(
    *,
    task_id: Optional[int],
    run_id: Optional[str],
    platform: str,
    pages_fetched: int,
    inserted_count: int,
    fetch_count: int,
    stop_reason: Optional[str],
    duration_sec: float,
) -> None:
    logger.info(
        "search_fetch_all_stop",
        extra={
            "task_id": task_id,
            "run_id": run_id,
            "platform": platform,
            "pages_fetched": int(pages_fetched),
            "inserted_count": int(inserted_count),
            "fetch_count": int(fetch_count),
            "stop_reason": stop_reason,
            "duration_sec": float(duration_sec),
        },
    )


def _log_date_filter_result(
    *,
    platform: str,
    page: int,
    records_total: int,
    records_after_date_filter: int,
    before_start_date_count: int,
    stop_reason: Optional[str],
) -> None:
    logger.info(
        "date_filter_result platform=%s page=%s records_total=%s "
        "records_after_date_filter=%s before_start_date_count=%s stop_reason=%s",
        platform,
        page,
        records_total,
        records_after_date_filter,
        before_start_date_count,
        stop_reason,
    )


def _allow_before_start_stop(*, platform: str, list_sort_type: Optional[int]) -> bool:
    """
    仅在明确“时间倒序”时，允许整页全部早于 start_date 后提前停止。
    - douyin/xhs/mp: sort_type=2 视为时间倒序
    - wxvideo: sort_type=1(最新) 视为时间倒序
    """
    if list_sort_type is None:
        return False
    p = (platform or "").strip().lower()
    if p == "wxvideo":
        return int(list_sort_type) == 1
    return int(list_sort_type) == 2


def _resolve_page_limit(mode: FetchAllMode) -> int:
    """``min(模式页数上限, 配置止损页数)``。"""
    base = mode.page_cap if mode.page_cap is not None else mode.safety_max_pages
    guard_cap = _guard_limits().max_pages
    return max(1, min(int(base), int(guard_cap)))


def _check_pre_page_guards(
    *,
    pages_fetched: int,
    page_limit: int,
    loop_started_monotonic: float,
    platform: str,
    fetch_count_cap: int,
    records_returned: int,
) -> Optional[str]:
    if pages_fetched >= page_limit:
        duration = time.monotonic() - loop_started_monotonic
        _log_fetch_structured(
            platform=platform,
            page=pages_fetched,
            pages_fetched=pages_fetched,
            records_returned=records_returned,
            fetch_count_cap=fetch_count_cap,
            has_more=True,
            duration_sec=duration,
            stop_reason=STOP_MAX_PAGES_REACHED,
        )
        return STOP_MAX_PAGES_REACHED
    max_run = _guard_limits().max_run_seconds
    if max_run is not None:
        duration = time.monotonic() - loop_started_monotonic
        if duration >= max_run:
            _log_fetch_structured(
                platform=platform,
                page=pages_fetched + 1,
                pages_fetched=pages_fetched,
                records_returned=records_returned,
                fetch_count_cap=fetch_count_cap,
                has_more=True,
                duration_sec=duration,
                stop_reason=STOP_MAX_RUN_SECONDS_REACHED,
            )
            return STOP_MAX_RUN_SECONDS_REACHED
    return None


def _evaluate_post_page_stop(
    *,
    platform: str,
    page_no: int,
    pages_fetched: int,
    current_run_inserted_count: int,
    fetch_count_cap: int,
    has_more: bool,
    raw_data: list[Any],
    new_chunk: list[dict[str, Any]],
    all_before_start_date: bool,
    allow_before_start_stop: bool,
    duplicate_pages_in_row: int,
    loop_started_monotonic: float,
    page_token: Optional[tuple[str, ...]] = None,
    seen_page_tokens: Optional[set[tuple[str, ...]]] = None,
    no_more: Optional[bool] = None,
) -> tuple[Optional[str], int]:
    """
    单页处理后的统一停止判定。
    返回 ``(stop_reason, updated_duplicate_pages_in_row)``。
    """
    duration = time.monotonic() - loop_started_monotonic
    dup_threshold = _guard_limits().duplicate_page_threshold

    if current_run_inserted_count >= fetch_count_cap:
        _log_fetch_structured(
            platform=platform,
            page=page_no,
            pages_fetched=pages_fetched,
            records_returned=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            duration_sec=duration,
            stop_reason=STOP_FETCH_COUNT_REACHED,
        )
        return STOP_FETCH_COUNT_REACHED, duplicate_pages_in_row

    if all_before_start_date and allow_before_start_stop:
        _log_fetch_structured(
            platform=platform,
            page=page_no,
            pages_fetched=pages_fetched,
            records_returned=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            duration_sec=duration,
            stop_reason=STOP_BEFORE_START_DATE,
        )
        return STOP_BEFORE_START_DATE, duplicate_pages_in_row

    if not raw_data:
        _log_fetch_structured(
            platform=platform,
            page=page_no,
            pages_fetched=pages_fetched,
            records_returned=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            duration_sec=duration,
            stop_reason=STOP_EMPTY_PAGE,
        )
        return STOP_EMPTY_PAGE, duplicate_pages_in_row

    if not new_chunk:
        end_of_pages = no_more if no_more is not None else (not has_more)
        if end_of_pages:
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages_fetched,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=has_more,
                duration_sec=duration,
                stop_reason=STOP_NO_MORE_DATA,
            )
            return STOP_NO_MORE_DATA, duplicate_pages_in_row
        duplicate_pages_in_row += 1
        if duplicate_pages_in_row >= dup_threshold:
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages_fetched,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=has_more,
                duration_sec=duration,
                stop_reason=STOP_DUPLICATE_PAGES_THRESHOLD,
            )
            return STOP_DUPLICATE_PAGES_THRESHOLD, duplicate_pages_in_row
    else:
        duplicate_pages_in_row = 0

    end_of_pages = (
        no_more if no_more is not None else (not has_more)
    )
    if end_of_pages:
        _log_fetch_structured(
            platform=platform,
            page=page_no,
            pages_fetched=pages_fetched,
            records_returned=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            duration_sec=duration,
            stop_reason=STOP_NO_MORE_DATA,
        )
        return STOP_NO_MORE_DATA, duplicate_pages_in_row

    if page_token is not None and seen_page_tokens is not None:
        if page_token in seen_page_tokens:
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages_fetched,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=has_more,
                duration_sec=duration,
                stop_reason=STOP_REPEATED_PAGE_TOKEN,
            )
            return STOP_REPEATED_PAGE_TOKEN, duplicate_pages_in_row
        seen_page_tokens.add(page_token)

    return None, duplicate_pages_in_row


def _finalize_meta_stop_reason(
    stop_reason: Optional[str],
    *,
    pages_fetched: int,
    page_limit: int,
) -> Optional[str]:
    if stop_reason:
        if stop_reason == "no_next_page":
            return STOP_NO_MORE_DATA
        if stop_reason == "page_limit_reached":
            return STOP_MAX_PAGES_REACHED
        return stop_reason
    if pages_fetched >= page_limit:
        return STOP_MAX_PAGES_REACHED
    return None


def _coerce_has_more_flag(value: Any, *, fallback: bool) -> bool:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) != 0
    s = str(value).strip().lower()
    if s in {"", "0", "false", "no", "none", "null"}:
        return False
    if s in {"1", "true", "yes"}:
        return True
    return fallback


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
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def yesterday_midnight_local() -> datetime:
    """本地日历「昨天 00:00:00」（naive）。"""
    now = datetime.now()
    y = now.date() - timedelta(days=1)
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
) -> list[dict[str, Any]]:
    """
    去掉本任务已见过的 ``note_id`` / ``aweme_id`` 等主键。

    不按 ``fetch_count`` 截断单页：接口若一次返回多于选择条数，全部保留；
    是否继续翻页由 ``fetch_count_cap`` 与 ``_evaluate_post_page_stop`` 决定。
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
    return out


def coerce_inserted_count(value: Any, *, fallback: int) -> int:
    if value is None:
        return max(0, int(fallback))
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return max(0, int(fallback))


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
    - 无显式日期且无 ``max_pages``：不按时间窗过滤（不会自动补默认时间段）。
    - 有显式 ``start_date`` / ``end_date``：时间窗模式（与 ``list_sort_type`` 无关）。
    - 仅有 ``max_pages``：纯页数上限模式。
    """
    has_dates = start_date is not None or end_date is not None
    has_max = max_pages is not None

    if not has_dates and not has_max:
        return FetchAllMode(
            use_date_window=False,
            start_ms=0,
            end_ms=2**63 - 1,
            page_cap=None,
            safety_max_pages=_configured_safety_max_pages(),
        )

    if not has_dates and has_max:
        # 纯页数：时间窗口占位，不使用
        user_cap = max(1, int(max_pages))
        guard_cap = _configured_safety_max_pages()
        effective = min(user_cap, guard_cap)
        return FetchAllMode(
            use_date_window=False,
            start_ms=0,
            end_ms=2**63 - 1,
            page_cap=effective,
            safety_max_pages=effective,
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
    safety = _configured_safety_max_pages()
    if max_pages is not None:
        cap = max(1, int(max_pages))

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
) -> tuple[list[dict[str, Any]], int, bool]:
    """
    按发布时间窗口过滤；假设 **新 → 旧** 排序。

    :return: (保留记录, 早于 start 的数量, 是否整页都早于 start)
    """
    kept: list[dict[str, Any]] = []
    before_start_date_count = 0
    records_total = 0
    for rec in records:
        if not isinstance(rec, dict):
            continue
        records_total += 1
        ts = publish_time_ms_from_record(rec)
        if ts is None:
            kept.append(rec)
            continue
        if ts > end_ms:
            continue
        if ts < start_ms:
            before_start_date_count += 1
            continue
        kept.append(rec)
    all_before_start_date = records_total > 0 and before_start_date_count == records_total
    return kept, before_start_date_count, all_before_start_date


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
    仅使用显式 ``start`` / ``end`` 时间边界；不再自动补默认时间窗。
    """
    if start_d is not None or end_d is not None:
        return start_d, end_d
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
    after_each_page: Optional[Callable[[list[dict[str, Any]]], Optional[int]]] = None,
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
        datetime.fromtimestamp(mode.start_ms / 1000.0) if mode.use_date_window else None
    )
    end_eff = (
        datetime.fromtimestamp(mode.end_ms / 1000.0) if mode.use_date_window else None
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
    stop_reason: Optional[str] = None
    current_run_inserted_count = 0

    platform = "douyin"
    page_limit = _resolve_page_limit(mode)
    loop_started = time.monotonic()
    seen_page_tokens: set[tuple[str, str]] = set()

    while True:
        pre_stop = _check_pre_page_guards(
            pages_fetched=pages,
            page_limit=page_limit,
            loop_started_monotonic=loop_started,
            platform=platform,
            fetch_count_cap=fetch_count_cap,
            records_returned=current_run_inserted_count,
        )
        if pre_stop:
            stop_reason = pre_stop
            break

        page_no = pages + 1
        remaining_in_run = fetch_count_cap - current_run_inserted_count
        if remaining_in_run <= 0:
            stop_reason = STOP_FETCH_COUNT_REACHED
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=True,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break

        result = api_call(api_url, key, body)
        if result.get("insufficient_balance"):
            insufficient_balance = True
            stop_reason = STOP_INSUFFICIENT_BALANCE
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=False,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break
        if result.get("error"):
            last_error = result["error"]
            stop_reason = STOP_API_ERROR
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=False,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break

        raw_data = result.get("data") or []
        if not isinstance(raw_data, list):
            raw_data = []
        next_cursor = str(result.get("next_cursor") or "")
        next_logid = str(result.get("next_logid") or "")
        has_more = _coerce_has_more_flag(
            result.get("has_more"),
            fallback=bool(next_cursor.strip() or next_logid.strip()),
        )
        balance = result.get("balance", balance)

        if mode.use_date_window:
            (
                chunk,
                before_start_count,
                all_before_start_date,
            ) = filter_records_by_publish_window(raw_data, mode.start_ms, mode.end_ms)
        else:
            chunk = [r for r in raw_data if isinstance(r, dict)]
            before_start_count = 0
            all_before_start_date = False

        allow_before_start_stop = _allow_before_start_stop(
            platform=platform, list_sort_type=list_sort_type
        )
        new_chunk = unique_new_records(chunk, seen_ids)
        _log_date_filter_result(
            platform=platform,
            page=page_no,
            records_total=len(raw_data),
            records_after_date_filter=len(chunk),
            before_start_date_count=before_start_count,
            stop_reason=(
                STOP_BEFORE_START_DATE
                if (all_before_start_date and allow_before_start_stop)
                else None
            ),
        )
        all_data.extend(new_chunk)
        pages += 1
        inserted_delta = len(new_chunk)
        if after_each_page is not None and new_chunk:
            inserted_delta = coerce_inserted_count(
                after_each_page(list(new_chunk)),
                fallback=len(new_chunk),
            )
        current_run_inserted_count += inserted_delta

        next_token: tuple[str, str] = (next_cursor.strip(), next_logid.strip())
        post_stop, duplicate_pages_in_row = _evaluate_post_page_stop(
            platform=platform,
            page_no=page_no,
            pages_fetched=pages,
            current_run_inserted_count=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            raw_data=raw_data,
            new_chunk=new_chunk,
            all_before_start_date=all_before_start_date,
            allow_before_start_stop=allow_before_start_stop,
            duplicate_pages_in_row=duplicate_pages_in_row,
            loop_started_monotonic=loop_started,
            page_token=next_token,
            seen_page_tokens=seen_page_tokens,
            no_more=not has_more,
        )
        if post_stop == STOP_BEFORE_START_DATE:
            stopped_before_start = True
        if post_stop:
            stop_reason = post_stop
            break

        _log_fetch_structured(
            platform=platform,
            page=page_no,
            pages_fetched=pages,
            records_returned=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            duration_sec=time.monotonic() - loop_started,
        )
        body = dict(body)
        body["cursor"] = next_cursor
        body["log_id"] = next_logid

    truncated = (
        pages >= page_limit
        and not stopped_before_start
        and last_error is None
        and not insufficient_balance
        and stop_reason in (None, STOP_MAX_PAGES_REACHED)
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
    meta["run_id"] = _get_run_id_for_log()
    meta["records_returned"] = current_run_inserted_count
    meta["max_success_count"] = current_run_inserted_count
    meta["stop_reason"] = _finalize_meta_stop_reason(
        stop_reason, pages_fetched=pages, page_limit=page_limit
    )
    meta["max_pages_effective"] = page_limit
    meta["max_run_seconds_effective"] = _guard_limits().max_run_seconds
    _log_search_fetch_all_stop(
        task_id=_get_task_id_for_log(),
        run_id=_get_run_id_for_log(),
        platform=platform,
        pages_fetched=pages,
        inserted_count=current_run_inserted_count,
        fetch_count=fetch_count_cap,
        stop_reason=meta.get("stop_reason"),
        duration_sec=time.monotonic() - loop_started,
    )

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
    after_each_page: Optional[Callable[[list[dict[str, Any]]], Optional[int]]] = None,
) -> dict[str, Any]:
    """小红书多页拉取（页码递增）。行为说明同 :func:`fetch_douyin_search_all`。"""
    fetch_count_cap = max(1, min(500, int(fetch_count_cap)))
    mode = resolve_fetch_all_mode(
        start_date=start_date,
        end_date=end_date,
        max_pages=max_pages,
        list_sort_type=list_sort_type,
    )
    start_eff = (
        datetime.fromtimestamp(mode.start_ms / 1000.0) if mode.use_date_window else None
    )
    end_eff = (
        datetime.fromtimestamp(mode.end_ms / 1000.0) if mode.use_date_window else None
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
    stop_reason: Optional[str] = None
    current_run_inserted_count = 0

    platform = "xhs"
    page_limit = _resolve_page_limit(mode)
    loop_started = time.monotonic()

    while True:
        pre_stop = _check_pre_page_guards(
            pages_fetched=pages,
            page_limit=page_limit,
            loop_started_monotonic=loop_started,
            platform=platform,
            fetch_count_cap=fetch_count_cap,
            records_returned=current_run_inserted_count,
        )
        if pre_stop:
            stop_reason = pre_stop
            break

        page_no = pages + 1
        remaining_in_run = fetch_count_cap - current_run_inserted_count
        if remaining_in_run <= 0:
            stop_reason = STOP_FETCH_COUNT_REACHED
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=True,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break

        body = dict(body_builder(params))
        body["page"] = start + pages
        body.pop("cursor", None)  # xhs: page-based pagination
        result = api_call(api_url, key, body)
        if result.get("insufficient_balance"):
            insufficient_balance = True
            stop_reason = STOP_INSUFFICIENT_BALANCE
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=False,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break
        if result.get("error"):
            last_error = result["error"]
            stop_reason = STOP_API_ERROR
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=False,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break

        raw_data = result.get("data") or []
        if not isinstance(raw_data, list):
            raw_data = []
        has_more = _coerce_has_more_flag(
            result.get("has_more"),
            fallback=bool(raw_data),
        )
        balance = result.get("balance", balance)

        if mode.use_date_window:
            (
                chunk,
                before_start_count,
                all_before_start_date,
            ) = filter_records_by_publish_window(raw_data, mode.start_ms, mode.end_ms)
        else:
            chunk = [r for r in raw_data if isinstance(r, dict)]
            before_start_count = 0
            all_before_start_date = False

        allow_before_start_stop = _allow_before_start_stop(
            platform=platform, list_sort_type=list_sort_type
        )
        new_chunk = unique_new_records(chunk, seen_ids)
        _log_date_filter_result(
            platform=platform,
            page=page_no,
            records_total=len(raw_data),
            records_after_date_filter=len(chunk),
            before_start_date_count=before_start_count,
            stop_reason=(
                STOP_BEFORE_START_DATE
                if (all_before_start_date and allow_before_start_stop)
                else None
            ),
        )
        all_data.extend(new_chunk)
        pages += 1
        inserted_delta = len(new_chunk)
        if after_each_page is not None and new_chunk:
            inserted_delta = coerce_inserted_count(
                after_each_page(list(new_chunk)),
                fallback=len(new_chunk),
            )
        current_run_inserted_count += inserted_delta

        post_stop, duplicate_pages_in_row = _evaluate_post_page_stop(
            platform=platform,
            page_no=page_no,
            pages_fetched=pages,
            current_run_inserted_count=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            raw_data=raw_data,
            new_chunk=new_chunk,
            all_before_start_date=all_before_start_date,
            allow_before_start_stop=allow_before_start_stop,
            duplicate_pages_in_row=duplicate_pages_in_row,
            loop_started_monotonic=loop_started,
            no_more=not has_more,
        )
        if post_stop == STOP_BEFORE_START_DATE:
            stopped_before_start = True
        if post_stop:
            stop_reason = post_stop
            break

        _log_fetch_structured(
            platform=platform,
            page=page_no,
            pages_fetched=pages,
            records_returned=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            duration_sec=time.monotonic() - loop_started,
        )

    truncated = (
        pages >= page_limit
        and not stopped_before_start
        and last_error is None
        and not insufficient_balance
        and stop_reason in (None, STOP_MAX_PAGES_REACHED)
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
    meta["run_id"] = _get_run_id_for_log()
    meta["records_returned"] = current_run_inserted_count
    meta["max_success_count"] = current_run_inserted_count
    meta["stop_reason"] = _finalize_meta_stop_reason(
        stop_reason, pages_fetched=pages, page_limit=page_limit
    )
    meta["max_pages_effective"] = page_limit
    meta["max_run_seconds_effective"] = _guard_limits().max_run_seconds
    _log_search_fetch_all_stop(
        task_id=_get_task_id_for_log(),
        run_id=_get_run_id_for_log(),
        platform=platform,
        pages_fetched=pages,
        inserted_count=current_run_inserted_count,
        fetch_count=fetch_count_cap,
        stop_reason=meta.get("stop_reason"),
        duration_sec=time.monotonic() - loop_started,
    )

    return {
        "records": all_data,
        "balance": balance,
        "insufficient_balance": insufficient_balance,
        "last_error": last_error,
        "meta": meta,
    }


def _apply_offset_cookies_pagination(
    body: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """视频号 / 公众号：用上一页 ``next_offset``、``cookies_buffer`` 更新请求体。"""
    out = dict(body)
    next_offset = result.get("next_offset")
    if next_offset is not None and str(next_offset).strip() != "":
        out["offset"] = next_offset
    cookies = result.get("cookies_buffer")
    if cookies is not None and str(cookies).strip() != "":
        out["cookies_buffer"] = cookies
    try:
        page_n = int(out.get("currentPage") or out.get("page") or 1)
    except (TypeError, ValueError):
        page_n = 1
    out["currentPage"] = page_n + 1
    out["page"] = page_n + 1
    return out


def _offset_pagination_exhausted(
    result: dict[str, Any], *, had_new_records: bool
) -> bool:
    """无下一页游标且无新 cookies 时视为翻页结束。"""
    next_offset = result.get("next_offset")
    cookies = result.get("cookies_buffer")
    has_offset = next_offset is not None and str(next_offset).strip() != ""
    has_cookies = cookies is not None and str(cookies).strip() != ""
    if has_offset or has_cookies:
        return False
    return not had_new_records


def fetch_offset_cookies_search_all(
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
    after_each_page: Optional[Callable[[list[dict[str, Any]]], Optional[int]]] = None,
    log_platform: str = "offset",
) -> dict[str, Any]:
    """
    视频号 / 公众号多页拉取（``offset`` + ``cookies_buffer`` 翻页）。

    行为说明同 :func:`fetch_douyin_search_all`；翻页字段由解析器写入 ``next_offset`` /
    ``cookies_buffer``。
    """
    fetch_count_cap = max(1, min(500, int(fetch_count_cap)))
    mode = resolve_fetch_all_mode(
        start_date=start_date,
        end_date=end_date,
        max_pages=max_pages,
        list_sort_type=list_sort_type,
    )
    start_eff = (
        datetime.fromtimestamp(mode.start_ms / 1000.0) if mode.use_date_window else None
    )
    end_eff = (
        datetime.fromtimestamp(mode.end_ms / 1000.0) if mode.use_date_window else None
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
    stop_reason: Optional[str] = None
    current_run_inserted_count = 0

    platform = log_platform
    page_limit = _resolve_page_limit(mode)
    loop_started = time.monotonic()
    seen_page_states: set[tuple[str, str]] = set()

    while True:
        pre_stop = _check_pre_page_guards(
            pages_fetched=pages,
            page_limit=page_limit,
            loop_started_monotonic=loop_started,
            platform=platform,
            fetch_count_cap=fetch_count_cap,
            records_returned=current_run_inserted_count,
        )
        if pre_stop:
            stop_reason = pre_stop
            break

        page_no = pages + 1
        remaining_in_run = fetch_count_cap - current_run_inserted_count
        if remaining_in_run <= 0:
            stop_reason = STOP_FETCH_COUNT_REACHED
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=True,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break

        result = api_call(api_url, key, body)
        if result.get("insufficient_balance"):
            insufficient_balance = True
            stop_reason = STOP_INSUFFICIENT_BALANCE
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=False,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break
        if result.get("error"):
            last_error = result["error"]
            stop_reason = STOP_API_ERROR
            _log_fetch_structured(
                platform=platform,
                page=page_no,
                pages_fetched=pages,
                records_returned=current_run_inserted_count,
                fetch_count_cap=fetch_count_cap,
                has_more=False,
                duration_sec=time.monotonic() - loop_started,
                stop_reason=stop_reason,
            )
            break

        raw_data = result.get("data") or []
        if not isinstance(raw_data, list):
            raw_data = []
        next_offset = str(result.get("next_offset") or "")
        next_cookies = str(result.get("cookies_buffer") or "")
        has_more = _coerce_has_more_flag(
            result.get("has_more"),
            fallback=bool(next_offset.strip() or next_cookies.strip()),
        )
        balance = result.get("balance", balance)

        if mode.use_date_window:
            (
                chunk,
                before_start_count,
                all_before_start_date,
            ) = filter_records_by_publish_window(raw_data, mode.start_ms, mode.end_ms)
        else:
            chunk = [r for r in raw_data if isinstance(r, dict)]
            before_start_count = 0
            all_before_start_date = False

        allow_before_start_stop = _allow_before_start_stop(
            platform=platform, list_sort_type=list_sort_type
        )
        new_chunk = unique_new_records(chunk, seen_ids)
        _log_date_filter_result(
            platform=platform,
            page=page_no,
            records_total=len(raw_data),
            records_after_date_filter=len(chunk),
            before_start_date_count=before_start_count,
            stop_reason=(
                STOP_BEFORE_START_DATE
                if (all_before_start_date and allow_before_start_stop)
                else None
            ),
        )
        all_data.extend(new_chunk)
        pages += 1
        inserted_delta = len(new_chunk)
        if after_each_page is not None and new_chunk:
            inserted_delta = coerce_inserted_count(
                after_each_page(list(new_chunk)),
                fallback=len(new_chunk),
            )
        current_run_inserted_count += inserted_delta

        page_state: tuple[str, str] = (next_offset.strip(), next_cookies.strip())
        offset_no_more = (not has_more) and _offset_pagination_exhausted(
            result, had_new_records=bool(new_chunk)
        )
        post_stop, duplicate_pages_in_row = _evaluate_post_page_stop(
            platform=platform,
            page_no=page_no,
            pages_fetched=pages,
            current_run_inserted_count=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            raw_data=raw_data,
            new_chunk=new_chunk,
            all_before_start_date=all_before_start_date,
            allow_before_start_stop=allow_before_start_stop,
            duplicate_pages_in_row=duplicate_pages_in_row,
            loop_started_monotonic=loop_started,
            page_token=page_state,
            seen_page_tokens=seen_page_states,
            no_more=offset_no_more,
        )
        if post_stop == STOP_BEFORE_START_DATE:
            stopped_before_start = True
        if post_stop:
            stop_reason = post_stop
            break

        _log_fetch_structured(
            platform=platform,
            page=page_no,
            pages_fetched=pages,
            records_returned=current_run_inserted_count,
            fetch_count_cap=fetch_count_cap,
            has_more=has_more,
            duration_sec=time.monotonic() - loop_started,
        )
        body = _apply_offset_cookies_pagination(body, result)

    truncated = (
        pages >= page_limit
        and not stopped_before_start
        and last_error is None
        and not insufficient_balance
        and stop_reason in (None, STOP_MAX_PAGES_REACHED)
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
    meta["run_id"] = _get_run_id_for_log()
    meta["records_returned"] = current_run_inserted_count
    meta["max_success_count"] = current_run_inserted_count
    meta["stop_reason"] = _finalize_meta_stop_reason(
        stop_reason, pages_fetched=pages, page_limit=page_limit
    )
    meta["max_pages_effective"] = page_limit
    meta["max_run_seconds_effective"] = _guard_limits().max_run_seconds
    _log_search_fetch_all_stop(
        task_id=_get_task_id_for_log(),
        run_id=_get_run_id_for_log(),
        platform=platform,
        pages_fetched=pages,
        inserted_count=current_run_inserted_count,
        fetch_count=fetch_count_cap,
        stop_reason=meta.get("stop_reason"),
        duration_sec=time.monotonic() - loop_started,
    )

    return {
        "records": all_data,
        "balance": balance,
        "insufficient_balance": insufficient_balance,
        "last_error": last_error,
        "meta": meta,
    }
