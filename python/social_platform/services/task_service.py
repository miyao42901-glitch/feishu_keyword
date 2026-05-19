from __future__ import annotations

import json
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
from social_platform.schemas.async_task import AsyncTaskStatusResponse
from social_platform.redis_client import ping_redis, redis_configured
from social_platform.services import async_task_redis
from social_platform.services.yddm_user_client import (
    YddmCallError,
    assert_x_user_id_matches_yddm,
)
from social_platform.utils.async_task_ids import parse_async_task_pk
from social_platform.schedule_time import (
    normalize_schedule_datetime,
    schedule_now_utc_naive,
)
from social_platform.utils.search_fetch_all import parse_optional_datetime

DEFAULT_INTERVAL_MINUTES = 60
MIN_INTERVAL_MINUTES = 5
DEFAULT_FETCH_COUNT = 100
MIN_FETCH_COUNT = 1
MAX_FETCH_COUNT = 500

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
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utc_now_naive() -> datetime:
    """异步任务窗口判断用的「当前时刻」（UTC naive）。"""
    return schedule_now_utc_naive()


def parse_task_schedule_times(
    task_start_time: Any,
    task_end_time: Any,
) -> tuple[datetime, datetime]:
    """解析前端传入的定时起止时间；无法解析时抛出 ValueError。"""
    start = parse_optional_datetime(task_start_time)
    end = parse_optional_datetime(task_end_time)
    if start is None or end is None:
        raise ValueError("task_start_time 与 task_end_time 为必填且须为合法时间")
    start_n = normalize_schedule_datetime(start)
    end_n = normalize_schedule_datetime(end)
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
    """Worker 执行用 body：search-all 注入本任务剩余可抓取数量。"""
    body = dict(task.body_json or {})
    action = (task.action or "").strip()
    if action in _SEARCH_ALL_PUBLIC_ACTIONS:
        total = normalize_fetch_count(task.fetch_count)
        done = max(0, int(task.success_count or 0))
        remaining = total - done
        body["fetch_count"] = max(1, remaining)
    return body


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.replace(microsecond=0).isoformat() + "Z"


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
    start = normalize_schedule_datetime(task.task_start_time)
    return start if start > t else t


def next_run_after_completion(
    task: AsyncTask,
    completed_at: datetime,
) -> Optional[datetime]:
    """本次采集结束后，若仍在窗口内则返回下次执行时刻，否则 None。"""
    if task.cancel_requested:
        return None
    end = normalize_schedule_datetime(task.task_end_time)
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
    end = normalize_schedule_datetime(row.task_end_time)
    if now >= end:
        return None

    target = (
        first_run_at(row, now=now)
        if run_at is None
        else normalize_schedule_datetime(run_at)
    )
    if target >= end:
        return None

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
    if task.cancel_requested:
        task.status = "cancelled"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        return False
    if (task.action or "").strip() in _SEARCH_ALL_PUBLIC_ACTIONS:
        max_fetch = normalize_fetch_count(task.fetch_count)
        success_done = max(0, int(task.success_count or 0))
        if success_done >= max_fetch:
            task.status = "success"
            task.update_time = datetime.utcnow()
            db.add(task)
            db.commit()
            return False

    done = completed_at if completed_at is not None else utc_now_naive()
    nxt = next_run_after_completion(task, done)
    if nxt is None:
        task.status = "success" if last_ok else "failed"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        return False

    task.status = "pending"
    task.update_time = datetime.utcnow()
    db.add(task)
    db.commit()
    key = (
        async_task_redis.get_cached_api_key(task_id)
        or str(getattr(task, "api_key", "") or "").strip()
        or (api_key or "").strip()
    )
    async_task_redis.enqueue_async_task_execution(task, api_key=key, run_at=nxt)
    return True


def submit_async_task(
    db: Session,
    *,
    action: str,
    body: dict[str, Any],
    user_id: str,
    api_key: str,
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

    row = AsyncTask(
        user_id=uid[:64],
        status="pending",
        action=action.strip()[:128],
        body_json=body_for_db,
        api_key=(api_key or "").strip()[:128],
        priority=pri,
        task_start_time=task_start_time,
        task_end_time=task_end_time,
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


def get_task_status(db: Session, task_id: str) -> Optional[AsyncTaskStatusResponse]:
    pk = parse_async_task_pk(task_id)
    if pk is None:
        return None
    row = db.get(AsyncTask, pk)
    if row is None:
        return None
    plat = platform_for_result_listing(row.action) or ""
    return AsyncTaskStatusResponse(
        task_id=int(row.id),
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
        interval_minutes=int(row.interval_minutes or 60),
        fetch_count=int(row.fetch_count or 100),
        create_time=_iso(row.create_time),
        update_time=_iso(row.update_time),
    )


def assert_async_task_user(*, api_key: str, x_user_id: str) -> str:
    """校验 X-API-Key / X-User-Id（yddm users/me），与提交异步任务一致。"""
    settings = get_settings()
    return assert_x_user_id_matches_yddm(
        settings, api_key=api_key, x_user_id=x_user_id
    )


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
    row.update_time = datetime.utcnow()
    db.add(row)
    db.commit()
    async_task_redis.retain_async_task_redis_on_cancel(row)
    if celery_id and was_active:
        from social_platform.tasks.celery_app import celery_app

        celery_app.control.revoke(celery_id, terminate=False)
    return "cancelled"


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
    if now >= normalize_schedule_datetime(row.task_end_time):
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
    row.error_message = None
    row.update_time = datetime.utcnow()
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
