from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional, Union

CancelAsyncTaskOutcome = Literal["cancelled", "already_cancelled"]
RestartAsyncTaskOutcome = Literal[
    "restarted", "already_active", "window_ended"
]


class AsyncTaskRestartResult:
    """restart_async_task 成功时的附带信息。"""

    def __init__(
        self,
        *,
        task_id: int,
        snapshot_source: str,
    ) -> None:
        self.task_id = int(task_id)
        self.snapshot_source = snapshot_source

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config.settings import get_settings
from social_platform.actions.registry import (
    body_dict_for_db,
    platform_for_result_listing,
    validate_body_for_action,
)
from social_platform.api_status_codes import (
    CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED,
    get_message,
)
from social_platform.models.async_task import AsyncTask
from social_platform.schemas.async_task import (
    AsyncTaskListResponse,
    AsyncTaskListSummary,
    AsyncTaskStatusResponse,
)
from social_platform.redis_client import ping_redis, redis_configured
from social_platform.services import async_task_redis
from social_platform.services.yddm_user_client import (
    YddmCallError,
    assert_x_user_id_matches_yddm,
)
from social_platform.utils.async_task_ids import parse_async_task_pk
from social_platform.schedule_time import (
    naive_dt,
    schedule_now_wall_naive,
    schedule_wall_clock_str,
)
from social_platform.utils.search_fetch_all import parse_optional_datetime

DEFAULT_INTERVAL_MINUTES = 60
MIN_INTERVAL_MINUTES = 5
DEFAULT_FETCH_COUNT = 100
MIN_FETCH_COUNT = 1
MAX_FETCH_COUNT = 500
MIN_TASK_NAME_LEN = 1
MAX_TASK_NAME_LEN = 100
logger = logging.getLogger(__name__)

_SEARCH_ALL_PUBLIC_ACTIONS = frozenset(
    {
        "douyin-search-all",
        "xhs-search-all",
        "wxvideo-search-all",
        "mp-search-all",
    }
)


class AsyncTaskDuplicateError(Exception):
    """相同用户、相同参数且仍在 pending/running 的异步任务已存在。"""

    def __init__(self, existing_task_id: int) -> None:
        self.existing_task_id = int(existing_task_id)
        super().__init__(str(self.existing_task_id))


def _utc_naive(dt: datetime) -> datetime:
    """与 ``naive_dt`` 一致（保留旧名供内部调用）。"""
    return naive_dt(dt)


def utc_now_naive() -> datetime:
    """异步任务调度用的「当前时刻」（东八区墙钟 naive，与库字段一致）。"""
    return schedule_now_wall_naive()


def parse_task_schedule_times(
    task_start_time: Any,
    task_end_time: Any,
) -> tuple[datetime, datetime]:
    """解析前端传入的定时起止时间；无法解析时抛出 ValueError。"""
    start = parse_optional_datetime(task_start_time)
    end = parse_optional_datetime(task_end_time)
    if start is None or end is None:
        raise ValueError("task_start_time 与 task_end_time 为必填且须为合法时间")
    start_n = naive_dt(start)
    end_n = naive_dt(end)
    if end_n <= start_n:
        raise ValueError("task_end_time 须晚于 task_start_time")
    now = utc_now_naive()
    if end_n <= now:
        raise ValueError("task_end_time 须晚于当前时间")
    return start_n, end_n


def normalize_interval_minutes(value: Any) -> int:
    """采集频率（分钟）：缺省 60，最小 5。"""
    if value is None:
        return DEFAULT_INTERVAL_MINUTES
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_INTERVAL_MINUTES
    return max(MIN_INTERVAL_MINUTES, n)


def interval_minutes_to_seconds(value: Any) -> int:
    """MySQL 存分钟；Redis 调度与到期判断使用秒。"""
    return normalize_interval_minutes(value) * 60


def normalize_fetch_count(value: Any) -> int:
    """单次采集条数：缺省 100，范围 1～500。"""
    if value is None:
        return DEFAULT_FETCH_COUNT
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_FETCH_COUNT
    return max(MIN_FETCH_COUNT, min(MAX_FETCH_COUNT, n))


def normalize_task_name(value: Any) -> str:
    """任务名称：去首尾空白，长度 1～100。"""
    if not isinstance(value, str):
        raise ValueError("task_name 长度须为 1～100 字符")
    name = value.strip()
    if len(name) < MIN_TASK_NAME_LEN or len(name) > MAX_TASK_NAME_LEN:
        raise ValueError("task_name 长度须为 1～100 字符")
    return name


def prepare_async_task_body(
    action: str,
    body: dict[str, Any],
    *,
    fetch_count: int,
) -> dict[str, Any]:
    """校验业务 body；fetch_count 仅存任务表，不入 body_json。"""
    cleaned = dict(body or {})
    cleaned.pop("fetch_count", None)
    validated = validate_body_for_action(action, cleaned)
    stored = body_dict_for_db(validated)
    stored.pop("fetch_count", None)
    return stored


def body_for_worker_execution(task: AsyncTask) -> dict[str, Any]:
    """Worker 执行用 body：search-all 注入「本轮」抓取上限。"""
    body = dict(task.body_json or {})
    action = (task.action or "").strip()
    if action in _SEARCH_ALL_PUBLIC_ACTIONS:
        body["fetch_count"] = normalize_fetch_count(task.fetch_count)
    return body


def _iso(dt: Optional[datetime]) -> Optional[str]:
    """API 调度时刻：``YYYY-MM-DD HH:MM:SS`` 墙钟字符串。"""
    return schedule_wall_clock_str(dt)


def _body_json_fingerprint(body: dict[str, Any]) -> str:
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _body_json_matches(stored: Any, expected: dict[str, Any]) -> bool:
    if not isinstance(stored, dict):
        stored = {}
    return _body_json_fingerprint(stored) == _body_json_fingerprint(expected)


def find_identical_async_task(
    db: Session,
    *,
    user_id: str,
    action: str,
    body_json: dict[str, Any],
    task_start_time: datetime,
    task_end_time: datetime,
    interval_minutes: int,
    fetch_count: int,
    priority: int,
) -> Optional[int]:
    """
    查询用户是否已有「参数完全一致」且仍在进行中的任务。

    比对字段：action、body_json、task_start/end、interval_minutes、fetch_count、priority。
    仅匹配 status 为 pending / running。
    """
    uid = (user_id or "").strip()
    if not uid:
        return None
    act = (action or "").strip()[:128]
    interval = normalize_interval_minutes(interval_minutes)
    fc = normalize_fetch_count(fetch_count)
    pri = max(0, min(9, int(priority)))
    start_n = _utc_naive(task_start_time)
    end_n = _utc_naive(task_end_time)

    stmt = (
        select(AsyncTask)
        .where(
            AsyncTask.user_id == uid,
            AsyncTask.action == act,
            AsyncTask.status.in_(("pending", "running")),
            AsyncTask.task_start_time == start_n,
            AsyncTask.task_end_time == end_n,
            AsyncTask.interval_minutes == interval,
            AsyncTask.fetch_count == fc,
            AsyncTask.priority == pri,
        )
        .order_by(AsyncTask.id.desc())
        .limit(20)
    )
    for row in db.scalars(stmt):
        if row is not None and _body_json_matches(row.body_json, body_json):
            return int(row.id)
    return None


def count_active_async_tasks(db: Session, user_id: str) -> int:
    uid = (user_id or "").strip()
    if not uid:
        return 0
    stmt = (
        select(func.count())
        .select_from(AsyncTask)
        .where(
            AsyncTask.user_id == uid,
            AsyncTask.status.in_(("pending", "running")),
        )
    )
    return int(db.scalar(stmt) or 0)


def first_run_at(task: AsyncTask, *, now: Optional[datetime] = None) -> datetime:
    """定时窗口内首次执行时刻：max(now, task_start_time)（均为 UTC naive）。"""
    t = now if now is not None else utc_now_naive()
    start = naive_dt(task.task_start_time)
    return start if start > t else t


def next_run_after_completion(
    task: AsyncTask,
    completed_at: datetime,
) -> Optional[datetime]:
    """本次采集结束后，若仍在窗口内则返回下次执行时刻，否则 None。"""
    if task.cancel_requested:
        return None
    end = naive_dt(task.task_end_time)
    done = _utc_naive(completed_at)
    if done >= end:
        return None
    interval = timedelta(minutes=normalize_interval_minutes(task.interval_minutes))
    nxt = done + interval
    if nxt >= end:
        return None
    return nxt


def redis_ready() -> bool:
    return redis_configured() and ping_redis()


def enqueue_async_task_run(
    db: Session,
    task_id: int,
    api_key: str,
    *,
    run_at: Optional[datetime] = None,
) -> Optional[str]:
    """Redis ZSET + Celery countdown 调度（不依赖 Beat 进程）。"""
    row = db.get(AsyncTask, task_id)
    if row is None:
        return None
    if row.cancel_requested:
        return None
    now = utc_now_naive()
    end = naive_dt(row.task_end_time)
    if now >= end:
        return None

    target = (
        first_run_at(row, now=now)
        if run_at is None
        else naive_dt(run_at)
    )
    if target >= end:
        return None

    row.next_run_at = target
    row.update_time = schedule_now_wall_naive()
    db.add(row)
    db.commit()

    key = (api_key or "").strip() or str(getattr(row, "api_key", "") or "").strip()
    return async_task_redis.enqueue_async_task_execution(row, api_key=key, run_at=target)


def schedule_next_async_run(
    db: Session,
    task_id: int,
    api_key: str,
    *,
    completed_at: Optional[datetime] = None,
    last_ok: bool = True,
) -> bool:
    """
    单次采集结束后：在 task_end 前按 interval_minutes 预约下一次 Celery；
    窗口结束则标记 success/failed 并返回 False。
    """
    task = db.get(AsyncTask, task_id)
    if task is None:
        return False

    def _log_schedule_next_decision(will_continue: bool) -> None:
        logger.info(
            "schedule_next_decision",
            extra={
                "task_id": int(task.id),
                "run_id": str(getattr(task, "current_run_id", "") or ""),
                "success_count": int(task.success_count or 0),
                "fetch_count_per_run": normalize_fetch_count(task.fetch_count),
                "task_end_time": schedule_wall_clock_str(task.task_end_time),
                "next_run_at": schedule_wall_clock_str(task.next_run_at),
                "will_continue_schedule": bool(will_continue),
            },
        )

    if task.cancel_requested:
        task.status = "cancelled"
        task.next_run_at = None
        task.current_run_id = None
        task.running_lease_until = None
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()
        _log_schedule_next_decision(False)
        return False

    done = completed_at if completed_at is not None else utc_now_naive()
    nxt = next_run_after_completion(task, done)
    if nxt is None:
        task.status = "success" if last_ok else "failed"
        task.next_run_at = None
        task.current_run_id = None
        task.running_lease_until = None
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()
        _log_schedule_next_decision(False)
        return False

    task.status = "pending"
    task.next_run_at = nxt
    task.celery_task_id = None
    task.current_run_id = None
    task.running_lease_until = None
    task.update_time = schedule_now_wall_naive()
    db.add(task)
    db.commit()
    key = (
        async_task_redis.get_cached_api_key(task_id)
        or str(getattr(task, "api_key", "") or "").strip()
        or (api_key or "").strip()
    )
    async_task_redis.enqueue_async_task_execution(task, api_key=key, run_at=nxt)
    _log_schedule_next_decision(True)
    return True


def submit_async_task(
    db: Session,
    *,
    action: str,
    body: dict[str, Any],
    user_id: str,
    api_key: str,
    task_name: str,
    task_start_time: datetime,
    task_end_time: datetime,
    interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
    fetch_count: int = DEFAULT_FETCH_COUNT,
    priority: int = 0,
) -> int:
    """写入 MySQL + Redis，并由 Redis ZSET + Beat 驱动周期 Celery 执行。"""
    if not redis_ready():
        raise RuntimeError(
            "Redis 未就绪：异步任务需 Redis 缓存与调度，请检查 REDIS_URL 并启动 Redis"
        )

    settings = get_settings()
    fc = normalize_fetch_count(fetch_count)
    body_for_db = prepare_async_task_body(action, body, fetch_count=fc)

    uid = assert_x_user_id_matches_yddm(settings, api_key=api_key, x_user_id=user_id)

    interval = normalize_interval_minutes(interval_minutes)
    pri = max(0, min(9, int(priority)))
    existing_id = find_identical_async_task(
        db,
        user_id=uid,
        action=action,
        body_json=body_for_db,
        task_start_time=task_start_time,
        task_end_time=task_end_time,
        interval_minutes=interval,
        fetch_count=fc,
        priority=pri,
    )
    if existing_id is not None:
        raise AsyncTaskDuplicateError(existing_id)

    max_active = max(1, int(settings.async_task_max_active_per_user))
    if count_active_async_tasks(db, uid) >= max_active:
        raise YddmCallError(
            api_code=CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED,
            http_status=429,
            message=get_message(CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED),
        )

    name = normalize_task_name(task_name)

    row = AsyncTask(
        user_id=uid[:64],
        task_name=name[:MAX_TASK_NAME_LEN],
        status="pending",
        action=action.strip()[:128],
        body_json=body_for_db,
        api_key=(api_key or "").strip()[:128],
        priority=pri,
        task_start_time=task_start_time,
        task_end_time=task_end_time,
        next_run_at=None,
        current_run_id=None,
        running_lease_until=None,
        interval_minutes=interval,
        fetch_count=fc,
    )
    db.add(row)
    db.flush()
    task_id = int(row.id)
    db.commit()

    row = db.get(AsyncTask, task_id)
    if row is not None:
        enqueue_async_task_run(db, task_id, str(row.api_key or "").strip())
    return task_id


def _async_task_row_to_status(row: AsyncTask) -> AsyncTaskStatusResponse:
    plat = platform_for_result_listing(row.action) or ""
    interval_min = int(row.interval_minutes or 60)
    return AsyncTaskStatusResponse(
        task_id=int(row.id),
        task_name=str(row.task_name or ""),
        user_id=row.user_id,
        platform=plat,
        status=row.status,
        action=row.action,
        error_message=row.error_message,
        celery_task_id=row.celery_task_id,
        priority=row.priority,
        cancel_requested=row.cancel_requested,
        success_count=int(row.success_count or 0),
        failed_count=int(row.failed_count or 0),
        task_start_time=_iso(row.task_start_time),
        task_end_time=_iso(row.task_end_time),
        next_run_at=_iso(row.next_run_at),
        current_run_id=row.current_run_id,
        running_lease_until=_iso(row.running_lease_until),
        interval_minutes=interval_min,
        fetch_count=int(row.fetch_count or 100),
        create_time=_iso(row.create_time),
        update_time=_iso(row.update_time),
    )


def get_task_status(db: Session, task_id: str) -> Optional[AsyncTaskStatusResponse]:
    pk = parse_async_task_pk(task_id)
    if pk is None:
        return None
    row = db.get(AsyncTask, pk)
    if row is None:
        return None
    return _async_task_row_to_status(row)


def list_async_tasks_for_user(
    db: Session,
    user_id: str,
    *,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
) -> AsyncTaskListResponse:
    """按 user_id 分页列出任务，并返回状态分布与采集计数汇总。"""
    uid = str(user_id or "").strip()
    page = max(1, int(page))
    limit = max(1, min(100, int(limit)))
    offset = (page - 1) * limit

    filters: list[Any] = [AsyncTask.user_id == uid]
    status_filter = (status or "").strip()
    if status_filter:
        filters.append(AsyncTask.status == status_filter)

    total = int(
        db.scalar(select(func.count()).select_from(AsyncTask).where(*filters)) or 0
    )

    status_rows = db.execute(
        select(AsyncTask.status, func.count())
        .where(AsyncTask.user_id == uid)
        .group_by(AsyncTask.status)
    ).all()
    counts: dict[str, int] = {str(s or ""): int(c or 0) for s, c in status_rows}

    sum_row = db.execute(
        select(
            func.coalesce(func.sum(AsyncTask.success_count), 0),
            func.coalesce(func.sum(AsyncTask.failed_count), 0),
        ).where(AsyncTask.user_id == uid)
    ).one()
    total_success_count = int(sum_row[0] or 0)
    total_failed_count = int(sum_row[1] or 0)

    pending_n = counts.get("pending", 0)
    running_n = counts.get("running", 0)
    summary = AsyncTaskListSummary(
        total=total,
        pending=pending_n,
        running=running_n,
        success=counts.get("success", 0),
        failed=counts.get("failed", 0),
        cancelled=counts.get("cancelled", 0),
        active=pending_n + running_n,
        total_success_count=total_success_count,
        total_failed_count=total_failed_count,
    )

    rows = db.scalars(
        select(AsyncTask)
        .where(*filters)
        .order_by(AsyncTask.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    items = [_async_task_row_to_status(r) for r in rows if r is not None]

    return AsyncTaskListResponse(
        page=page,
        limit=limit,
        summary=summary,
        items=items,
    )


def assert_async_task_user(*, api_key: str, x_user_id: str) -> str:
    """校验 X-API-Key / X-User-Id（yddm users/me），与提交异步任务一致。"""
    settings = get_settings()
    return assert_x_user_id_matches_yddm(
        settings, api_key=api_key, x_user_id=x_user_id
    )


def assert_async_task_auth_token(*, auth_token: str, x_user_id: str) -> str:
    """校验 X-Auth-Token / X-User-Id（与 X-API-Key 相同，走 yddm users/me）。"""
    return assert_async_task_user(api_key=auth_token, x_user_id=x_user_id)


def update_async_task(
    db: Session,
    task_id: str,
    *,
    user_id: str,
    updates: dict[str, Any],
) -> Optional[AsyncTaskStatusResponse]:
    """
    按任务 ID 部分更新字段；返回 None 表示任务不存在。
    用户不一致时抛出 ApiHttpError(403)。
    """
    from social_platform.api_response import ApiHttpError
    from social_platform.api_status_codes import CODE_ASYNC_SUBMIT_USER_MISMATCH

    if not updates:
        raise ValueError("至少提供一个要修改的字段")

    pk = parse_async_task_pk(task_id)
    if pk is None:
        return None
    row = db.get(AsyncTask, pk)
    if row is None:
        return None

    uid = str(user_id or "").strip()
    if uid and str(row.user_id or "").strip() != uid:
        raise ApiHttpError(
            CODE_ASYNC_SUBMIT_USER_MISMATCH,
            http_status=403,
        )

    changed: dict[str, Any] = {}
    schedule_fields = {"interval_minutes", "fetch_count", "task_start_time", "task_end_time", "priority"}
    wants_schedule = bool(schedule_fields.intersection(updates))
    if wants_schedule and row.status != "pending":
        raise ValueError("仅 pending 状态的任务可修改调度相关字段")

    if "task_name" in updates:
        row.task_name = normalize_task_name(updates["task_name"])[:MAX_TASK_NAME_LEN]
        changed["task_name"] = row.task_name

    if "interval_minutes" in updates:
        row.interval_minutes = normalize_interval_minutes(updates["interval_minutes"])
        changed["interval_minutes"] = int(row.interval_minutes)

    if "fetch_count" in updates:
        row.fetch_count = normalize_fetch_count(updates["fetch_count"])
        changed["fetch_count"] = int(row.fetch_count)

    if "priority" in updates:
        row.priority = max(0, min(9, int(updates["priority"])))
        changed["priority"] = int(row.priority)

    if "task_start_time" in updates or "task_end_time" in updates:
        start_raw = updates.get("task_start_time", row.task_start_time)
        end_raw = updates.get("task_end_time", row.task_end_time)
        start_parsed = parse_optional_datetime(start_raw)
        end_parsed = parse_optional_datetime(end_raw)
        if start_parsed is None or end_parsed is None:
            raise ValueError("task_start_time 与 task_end_time 须为合法时间")
        start_n = naive_dt(start_parsed)
        end_n = naive_dt(end_parsed)
        if end_n <= start_n:
            raise ValueError("task_end_time 须晚于 task_start_time")
        now = utc_now_naive()
        if end_n <= now:
            raise ValueError("task_end_time 须晚于当前时间")
        if "task_start_time" in updates:
            row.task_start_time = start_n
            changed["task_start_time"] = schedule_wall_clock_str(start_n)
        if "task_end_time" in updates:
            row.task_end_time = end_n
            changed["task_end_time"] = schedule_wall_clock_str(end_n)

    if not changed:
        raise ValueError("至少提供一个要修改的字段")

    row.update_time = schedule_now_wall_naive()
    db.add(row)
    db.commit()

    logger.info(
        "async_task_edited user_id=%s task_id=%s fields=%s values=%s at=%s",
        uid,
        pk,
        list(changed.keys()),
        changed,
        schedule_wall_clock_str(row.update_time),
    )

    row = db.get(AsyncTask, pk)
    if row is None:
        return None
    return _async_task_row_to_status(row)


def _revoke_celery_task(celery_id: Optional[str], *, terminate: bool = False) -> None:
    cid = (celery_id or "").strip()
    if not cid:
        return
    from social_platform.tasks.celery_app import celery_app

    celery_app.control.revoke(cid, terminate=terminate)


def cancel_async_task(
    db: Session, task_id: str, *, user_id: str
) -> Optional[CancelAsyncTaskOutcome]:
    """
    取消异步任务：校验归属用户，MySQL 置 cancelled；Redis 快照保留 1 天（不删 api_key）。
    返回 None 表示任务不存在；already_cancelled 表示已取消无需重复操作。
    用户不一致抛出 ApiHttpError(403)。
    """
    from social_platform.api_response import ApiHttpError
    from social_platform.api_status_codes import CODE_ASYNC_SUBMIT_USER_MISMATCH

    pk = parse_async_task_pk(task_id)
    if pk is None:
        return None
    row = db.get(AsyncTask, pk)
    if row is None:
        return None
    uid = str(user_id or "").strip()
    if uid and str(row.user_id or "").strip() != uid:
        raise ApiHttpError(
            CODE_ASYNC_SUBMIT_USER_MISMATCH,
            http_status=403,
        )
    if row.status == "cancelled" or row.cancel_requested:
        return "already_cancelled"

    celery_id = row.celery_task_id
    was_active = row.status in ("pending", "running")
    row.cancel_requested = True
    row.status = "cancelled"
    row.next_run_at = None
    row.current_run_id = None
    row.running_lease_until = None
    row.update_time = schedule_now_wall_naive()
    db.add(row)
    db.commit()
    async_task_redis.retain_async_task_redis_on_cancel(row)
    if celery_id and was_active:
        _revoke_celery_task(celery_id, terminate=False)
    return "cancelled"


def delete_async_task(db: Session, task_id: str, *, user_id: str) -> bool:
    """
    删除异步任务：从 Redis 调度中移除、撤销 Celery 消息/执行，并删除 MySQL 任务行。
    关联采集结果表因外键 ON DELETE CASCADE 一并删除。
    任意 status（含 cancelled）均可删除；不调用 yddm，仅比对库中 user_id。
    返回 False 表示任务不存在；用户不一致抛出 ApiHttpError(403)。
    """
    from social_platform.api_response import ApiHttpError
    from social_platform.api_status_codes import CODE_ASYNC_SUBMIT_USER_MISMATCH

    pk = parse_async_task_pk(task_id)
    if pk is None:
        return False
    row = db.get(AsyncTask, pk)
    if row is None:
        return False

    uid = str(user_id or "").strip()
    if uid and str(row.user_id or "").strip() != uid:
        raise ApiHttpError(
            CODE_ASYNC_SUBMIT_USER_MISMATCH,
            http_status=403,
        )

    celery_id = row.celery_task_id
    was_active = row.status in ("pending", "running")
    terminate = row.status == "running"
    task_name = str(row.task_name or "")
    action = str(row.action or "")
    status = str(row.status or "")

    async_task_redis.delete_async_task_redis(pk)
    if celery_id and was_active:
        _revoke_celery_task(celery_id, terminate=terminate)

    db.delete(row)
    db.commit()

    logger.info(
        "async_task_deleted user_id=%s task_id=%s task_name=%s action=%s status=%s celery_revoked=%s",
        uid,
        pk,
        task_name,
        action,
        status,
        bool(celery_id and was_active),
    )
    return True


def restart_async_task(
    db: Session,
    task_id: str,
    *,
    user_id: str,
    api_key: str,
) -> Optional[Union[RestartAsyncTaskOutcome, AsyncTaskRestartResult]]:
    """
    重启已结束或已取消的异步任务：恢复 pending 并重新入队。
    成功/失败计数与基础信息优先读 Redis 快照，否则用 MySQL 任务行。
    返回 None 表示任务不存在；``already_active`` / ``window_ended`` 为不可重启；
    成功时返回 ``AsyncTaskRestartResult``。用户不一致抛出 ApiHttpError(403)。
    """
    from social_platform.api_response import ApiHttpError
    from social_platform.api_status_codes import CODE_ASYNC_SUBMIT_USER_MISMATCH

    if not redis_ready():
        raise RuntimeError(
            "Redis 未就绪：异步任务需 Redis 缓存与调度，请检查 REDIS_URL"
        )

    pk = parse_async_task_pk(task_id)
    if pk is None:
        return None
    row = db.get(AsyncTask, pk)
    if row is None:
        return None
    uid = str(user_id or "").strip()
    if uid and str(row.user_id or "").strip() != uid:
        raise ApiHttpError(
            CODE_ASYNC_SUBMIT_USER_MISMATCH,
            http_status=403,
        )

    if row.status in ("pending", "running"):
        return "already_active"

    now = utc_now_naive()
    if now >= naive_dt(row.task_end_time):
        return "window_ended"

    settings = get_settings()
    max_active = max(1, int(settings.async_task_max_active_per_user))
    if count_active_async_tasks(db, uid) >= max_active:
        raise YddmCallError(
            api_code=CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED,
            http_status=429,
            message=get_message(CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED),
        )

    snap = async_task_redis.load_async_task_restart_snapshot(pk, row)
    row.success_count = int(snap["success_count"])
    row.failed_count = int(snap["failed_count"])
    row.cancel_requested = False
    row.status = "pending"
    row.celery_task_id = None
    row.next_run_at = None
    row.current_run_id = None
    row.running_lease_until = None
    row.error_message = None
    row.update_time = schedule_now_wall_naive()
    db.add(row)
    db.commit()

    row = db.get(AsyncTask, pk)
    if row is not None:
        row.api_key = (api_key or "").strip()[:128]
        db.add(row)
        db.commit()
        enqueue_async_task_run(db, pk, str(row.api_key or "").strip())
    return AsyncTaskRestartResult(
        task_id=pk,
        snapshot_source=str(snap.get("source") or "mysql"),
    )


def request_cancel(db: Session, task_id: str) -> bool:
    """内部取消（不校验 yddm）；HTTP 请使用 cancel_async_task。"""
    pk = parse_async_task_pk(task_id)
    if pk is None:
        return False
    row = db.get(AsyncTask, pk)
    if row is None:
        return False
    outcome = cancel_async_task(db, task_id, user_id=str(row.user_id or ""))
    return outcome is not None


def database_configured() -> bool:
    return bool(get_settings().database_url.strip())
