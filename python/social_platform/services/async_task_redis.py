"""异步任务 Redis 缓存 + ZSET 定时调度（HTTP 轮询 / Celery Beat / countdown 多路投递）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select

from social_platform.models.async_task import AsyncTask
from social_platform.redis_client import get_redis, redis_configured
from social_platform.schedule_time import (
    normalize_schedule_datetime,
    parse_schedule_utc_iso,
    schedule_now_utc_naive,
    schedule_utc_iso,
)

logger = logging.getLogger(__name__)

TASK_KEY_PREFIX = "feishu:async:task:"
API_KEY_PREFIX = "feishu:async:api_key:"
SCHEDULE_ZSET = "feishu:async:schedule"
DISPATCH_LOCK_PREFIX = "feishu:async:dispatching:"
RESTORE_LOCK_KEY = "feishu:async:restore:worker_ready_lock"
# 取消后任务快照 / api_key 保留时长（便于重启时读取 success_count 等）
CANCELLED_TASK_CACHE_TTL_SECONDS = 86400


def _task_key(task_id: int) -> str:
    return f"{TASK_KEY_PREFIX}{int(task_id)}"


def _api_key_key(task_id: int) -> str:
    return f"{API_KEY_PREFIX}{int(task_id)}"


def _dispatch_lock_key(task_id: int) -> str:
    return f"{DISPATCH_LOCK_PREFIX}{int(task_id)}"


def _dispatch_lock_ttl_seconds() -> int:
    from config.settings import get_settings

    return max(60, int(get_settings().async_dispatch_lock_ttl_seconds))


def _ttl_seconds(task_end: datetime, *, extra: int = 3600) -> int:
    from config.settings import get_settings

    end = normalize_schedule_datetime(task_end)
    now = schedule_now_utc_naive()
    raw = max(60, int((end - now).total_seconds()) + extra)
    max_ttl = max(60, int(get_settings().async_task_redis_max_ttl_seconds))
    return min(raw, max_ttl)


def _log_cleanup_schedule_member(task_id: int, reason: str) -> None:
    logger.info(
        "cleanup_schedule_member",
        extra={
            "task_id": int(task_id),
            "reason": str(reason),
            "cleaned_schedule_member": 1,
        },
    )


def parse_cached_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return normalize_schedule_datetime(value)
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        return parse_schedule_utc_iso(raw)
    try:
        return normalize_schedule_datetime(datetime.fromisoformat(raw))
    except ValueError:
        return None


def is_run_at_due(run_at: datetime, *, now: Optional[datetime] = None) -> bool:
    """判断 scheduled run_at 是否已到（参数均为 UTC naive）。"""
    t = now if now is not None else schedule_now_utc_naive()
    at = (
        run_at.astimezone(timezone.utc).replace(tzinfo=None)
        if run_at.tzinfo
        else run_at.replace(tzinfo=None)
    )
    return at <= t


def resolve_next_run_at(
    row: AsyncTask,
    *,
    cached: Optional[dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> datetime:
    """解析任务下一次应执行时刻：优先 Redis 缓存的 next_run_at，否则窗口内首次执行。"""
    from social_platform.services.task_service import first_run_at

    t = now if now is not None else schedule_now_utc_naive()
    if cached:
        nxt = parse_cached_datetime(cached.get("next_run_at"))
        if nxt is not None:
            start = first_run_at(row, now=t)
            return nxt if nxt >= start else start
    return first_run_at(row, now=t)


def _row_to_cache(
    row: AsyncTask,
    *,
    next_run_at: Optional[datetime] = None,
    clear_next_run: bool = False,
    previous: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    from social_platform.services.task_service import interval_minutes_to_seconds

    interval_min = int(getattr(row, "interval_minutes", None) or 60)
    payload: dict[str, Any] = {
        "task_id": int(row.id),
        "user_id": row.user_id,
        "status": row.status,
        "action": row.action,
        "body_json": row.body_json if isinstance(row.body_json, dict) else {},
        "error_message": row.error_message,
        "celery_task_id": row.celery_task_id,
        "priority": int(row.priority or 0),
        "cancel_requested": bool(row.cancel_requested),
        "success_count": int(row.success_count or 0),
        "failed_count": int(row.failed_count or 0),
        "task_start_time": (
            row.task_start_time.isoformat() if row.task_start_time else None
        ),
        "task_end_time": row.task_end_time.isoformat() if row.task_end_time else None,
        "interval_minutes": interval_min,
        "interval_seconds": interval_minutes_to_seconds(interval_min),
        "fetch_count": int(getattr(row, "fetch_count", None) or 100),
    }
    if clear_next_run or row.status == "running":
        return payload
    if next_run_at is not None:
        payload["next_run_at"] = schedule_utc_iso(next_run_at)
    elif previous and previous.get("next_run_at"):
        payload["next_run_at"] = previous["next_run_at"]
    return payload


def cache_async_task(
    row: AsyncTask,
    *,
    api_key: str,
    next_run_at: Optional[datetime] = None,
) -> None:
    """写入任务快照与执行用 API Key（TTL 至窗口结束）。"""
    if not redis_configured():
        return
    r = get_redis()
    tid = int(row.id)
    ttl = _ttl_seconds(row.task_end_time)
    previous = get_cached_async_task(tid)
    payload = _row_to_cache(row, next_run_at=next_run_at, previous=previous)
    r.setex(_task_key(tid), ttl, json.dumps(payload, ensure_ascii=False))
    key = (api_key or "").strip()
    if key:
        r.setex(_api_key_key(tid), ttl, key)


def update_async_task_cache(
    row: AsyncTask,
    *,
    next_run_at: Optional[datetime] = None,
    clear_next_run: bool = False,
) -> None:
    if not redis_configured():
        return
    r = get_redis()
    tid = int(row.id)
    ttl = _ttl_seconds(row.task_end_time)
    previous = get_cached_async_task(tid)
    payload = _row_to_cache(
        row,
        next_run_at=next_run_at,
        clear_next_run=clear_next_run,
        previous=previous,
    )
    r.setex(_task_key(tid), ttl, json.dumps(payload, ensure_ascii=False))


def get_cached_async_task(task_id: int) -> Optional[dict[str, Any]]:
    if not redis_configured():
        return None
    raw = get_redis().get(_task_key(task_id))
    if not raw:
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def get_cached_api_key(task_id: int) -> Optional[str]:
    if not redis_configured():
        return None
    v = get_redis().get(_api_key_key(int(task_id)))
    return (v or "").strip() or None


def _hydrate_cached_api_key(task_id: int, api_key: str, task_end: datetime) -> None:
    """将 DB 中 api_key 回填到 Redis（用于重启/缓存丢失后的恢复）。"""
    if not redis_configured():
        return
    key = (api_key or "").strip()
    if not key:
        return
    ttl = _ttl_seconds(task_end)
    get_redis().setex(_api_key_key(int(task_id)), ttl, key)


def resolve_api_key_for_task(*, task_id: int, row: Optional[AsyncTask] = None) -> Optional[str]:
    """任务执行 api_key 解析：优先 Redis，缺失时回退 MySQL 并回填 Redis。"""
    cached = get_cached_api_key(task_id)
    if cached:
        return cached
    target = row
    if target is None:
        from social_platform.database.session import session_scope

        with session_scope() as db:
            target = db.get(AsyncTask, int(task_id))
    if target is None:
        return None
    db_key = str(getattr(target, "api_key", "") or "").strip()
    if not db_key:
        return None
    _hydrate_cached_api_key(int(task_id), db_key, target.task_end_time)
    return db_key


def schedule_async_task_run(task_id: int, run_at: datetime) -> None:
    """将任务加入 Redis 调度 ZSET（score = 执行时刻 Unix 秒）。"""
    if not redis_configured():
        raise RuntimeError("Redis 未配置，无法调度异步任务")
    score = normalize_schedule_datetime(run_at).timestamp()
    get_redis().zadd(SCHEDULE_ZSET, {str(int(task_id)): score})


def unschedule_async_task(task_id: int) -> None:
    if not redis_configured():
        return
    get_redis().zrem(SCHEDULE_ZSET, str(int(task_id)))


def delete_async_task_redis(task_id: int) -> None:
    """彻底删除任务 Redis 数据（调度、快照、api_key、投递锁）。"""
    if not redis_configured():
        return
    r = get_redis()
    tid = int(task_id)
    r.zrem(SCHEDULE_ZSET, str(tid))
    r.delete(_task_key(tid), _api_key_key(tid), _dispatch_lock_key(tid))


def retain_async_task_redis_on_cancel(row: AsyncTask) -> None:
    """
    取消任务：移出调度 ZSET，任务快照与 api_key 保留 ``CANCELLED_TASK_CACHE_TTL_SECONDS``（默认 1 天）。
    """
    if not redis_configured():
        return
    r = get_redis()
    tid = int(row.id)
    r.zrem(SCHEDULE_ZSET, str(tid))
    r.delete(_dispatch_lock_key(tid))
    previous = get_cached_async_task(tid)
    api_key = get_cached_api_key(tid) or str(getattr(row, "api_key", "") or "").strip()
    payload = _row_to_cache(row, clear_next_run=True, previous=previous)
    ttl = CANCELLED_TASK_CACHE_TTL_SECONDS
    r.setex(_task_key(tid), ttl, json.dumps(payload, ensure_ascii=False))
    if api_key:
        r.setex(_api_key_key(tid), ttl, api_key)


def restart_snapshot_from_cache(cached: dict[str, Any]) -> dict[str, Any]:
    """从 Redis 任务快照解析重启所需字段。"""
    body = cached.get("body_json")
    if not isinstance(body, dict):
        body = {}
    return {
        "success_count": int(cached.get("success_count") or 0),
        "failed_count": int(cached.get("failed_count") or 0),
        "action": str(cached.get("action") or ""),
        "body_json": body,
        "interval_minutes": cached.get("interval_minutes"),
        "fetch_count": cached.get("fetch_count"),
        "priority": cached.get("priority"),
        "task_start_time": cached.get("task_start_time"),
        "task_end_time": cached.get("task_end_time"),
        "source": "redis",
    }


def restart_snapshot_from_row(row: AsyncTask) -> dict[str, Any]:
    """从 MySQL 任务行解析重启所需字段。"""
    return {
        "success_count": int(row.success_count or 0),
        "failed_count": int(row.failed_count or 0),
        "action": str(row.action or ""),
        "body_json": dict(row.body_json or {}) if isinstance(row.body_json, dict) else {},
        "interval_minutes": int(row.interval_minutes or 60),
        "fetch_count": int(getattr(row, "fetch_count", None) or 100),
        "priority": int(row.priority or 0),
        "task_start_time": row.task_start_time.isoformat() if row.task_start_time else None,
        "task_end_time": row.task_end_time.isoformat() if row.task_end_time else None,
        "source": "mysql",
    }


def load_async_task_restart_snapshot(
    task_id: int, row: AsyncTask
) -> dict[str, Any]:
    """优先 Redis 快照，缺失时回退 MySQL 行。"""
    cached = get_cached_async_task(task_id)
    if cached:
        snap = restart_snapshot_from_cache(cached)
        if snap.get("action"):
            return snap
    return restart_snapshot_from_row(row)


def apply_celery_run_at(
    task_id: int,
    api_key: str,
    run_at: datetime,
    *,
    priority: int = 0,
) -> Optional[str]:
    """
    通过 Celery countdown 预约执行（不依赖 Beat）。
    返回 Celery task id。
    """
    from social_platform.tasks.worker_tasks import run_social_async_task

    key = (api_key or "").strip()
    if not key:
        return None
    now = schedule_now_utc_naive()
    target = normalize_schedule_datetime(run_at)
    countdown = max(0, int((target - now).total_seconds()))
    kwargs: dict[str, Any] = {
        "args": [int(task_id), key],
        "priority": int(priority),
    }
    if countdown > 0:
        kwargs["countdown"] = countdown
    async_result = run_social_async_task.apply_async(**kwargs)
    cid = async_result.id[:128] if async_result.id else None
    if cid:
        _persist_celery_task_id(task_id, cid)
    return cid


def _persist_celery_task_id(task_id: int, celery_task_id: str) -> None:
    from social_platform.database.session import session_scope

    with session_scope() as db:
        row = db.get(AsyncTask, int(task_id))
        if row is not None:
            row.celery_task_id = celery_task_id
            row.update_time = datetime.utcnow()
            db.add(row)
    update_cached_celery_id(task_id, celery_task_id)


def dispatch_task_by_id(task_id: int) -> Optional[str]:
    """立即将单任务投递到 Celery（优先 Redis，缺失回退 MySQL api_key）。"""
    if not redis_configured():
        return None
    r = get_redis()
    lock_key = _dispatch_lock_key(task_id)
    lock_ttl = _dispatch_lock_ttl_seconds()
    if not r.set(lock_key, "1", nx=True, ex=lock_ttl):
        ttl = int(r.ttl(lock_key) or -2)
        if ttl <= 0:
            logger.warning(
                "stale_dispatch_lock",
                extra={"task_id": int(task_id), "stale_dispatch_lock": 1, "ttl": ttl},
            )
            r.delete(lock_key)
            if not r.set(lock_key, "1", nx=True, ex=lock_ttl):
                logger.info(
                    "dispatch_locked",
                    extra={"task_id": int(task_id), "dispatch_locked": 1},
                )
                return None
        else:
            logger.info(
                "dispatch_locked",
                extra={"task_id": int(task_id), "dispatch_locked": 1, "ttl": ttl},
            )
            return None

    from social_platform.database.session import session_scope

    try:
        priority = 0
        api_key: Optional[str] = None
        with session_scope() as db:
            row = db.get(AsyncTask, int(task_id))
            if row is None:
                unschedule_async_task(task_id)
                _log_cleanup_schedule_member(task_id, "task_not_found")
                return None
            if row.cancel_requested or str(row.status or "") in ("cancelled", "success"):
                unschedule_async_task(task_id)
                _log_cleanup_schedule_member(task_id, f"status_{row.status}")
                return None
            if row.status == "running":
                return row.celery_task_id
            now = schedule_now_utc_naive()
            if now >= normalize_schedule_datetime(row.task_end_time):
                unschedule_async_task(task_id)
                _log_cleanup_schedule_member(task_id, "task_window_ended")
                return None
            api_key = resolve_api_key_for_task(task_id=task_id, row=row)
            if not api_key:
                logger.warning("async task %s missing api_key in redis and mysql", task_id)
                return None
            cached = get_cached_async_task(task_id)
            run_at = resolve_next_run_at(row, cached=cached, now=now)
            if not is_run_at_due(run_at, now=now):
                schedule_async_task_run(task_id, run_at)
                return None
            priority = int(row.priority or 0)

        cid = apply_celery_run_at(
            task_id, str(api_key or ""), schedule_now_utc_naive(), priority=priority
        )
        return cid
    finally:
        r.delete(lock_key)


def update_cached_celery_id(task_id: int, celery_task_id: str) -> None:
    cached = get_cached_async_task(task_id)
    if cached is None:
        return
    cached["celery_task_id"] = celery_task_id
    r = get_redis()
    key = _task_key(task_id)
    ttl = r.ttl(key)
    if ttl and ttl > 0:
        r.setex(key, int(ttl), json.dumps(cached, ensure_ascii=False))


def dispatch_due_async_tasks(*, batch_size: int = 50) -> int:
    """
    扫描 Redis ZSET 中已到期的 task_id 并投递 Worker。
    可由 HTTP 后台线程或 Celery Beat 调用。
    """
    if not redis_configured():
        return 0
    r = get_redis()
    now = schedule_now_utc_naive().timestamp()
    members = r.zrangebyscore(SCHEDULE_ZSET, "-inf", now, start=0, num=batch_size)
    dispatched = 0
    from social_platform.database.session import session_scope

    for member in members:
        try:
            tid = int(member)
        except (TypeError, ValueError):
            r.zrem(SCHEDULE_ZSET, member)
            continue
        if not r.zrem(SCHEDULE_ZSET, member):
            continue
        cid = dispatch_task_by_id(tid)
        if cid:
            dispatched += 1
        else:
            should_cleanup = False
            cleanup_reason = ""
            with session_scope() as db:
                row = db.get(AsyncTask, int(tid))
                if row is None:
                    should_cleanup = True
                    cleanup_reason = "task_not_found"
                else:
                    status = str(row.status or "")
                    if status in ("success", "cancelled") or row.cancel_requested:
                        should_cleanup = True
                        cleanup_reason = f"status_{status}"
                    elif now >= normalize_schedule_datetime(row.task_end_time).timestamp():
                        should_cleanup = True
                        cleanup_reason = "task_window_ended"
            if should_cleanup:
                _log_cleanup_schedule_member(tid, cleanup_reason)
                continue
            cached = get_cached_async_task(tid)
            defer = now + 30
            if cached:
                nxt = parse_cached_datetime(cached.get("next_run_at"))
                if nxt is not None and nxt.timestamp() > now:
                    defer = nxt.timestamp()
            r.zadd(SCHEDULE_ZSET, {member: defer})
            logger.info("async task %s dispatch deferred, re-queued at %s", tid, defer)
    return dispatched


def recover_stale_running_tasks(*, batch_size: int = 50) -> int:
    """
    补救：长时间处于 running（Worker 崩溃或 schedule 失败）的任务重置为 pending 并重新入队。
    """
    if not redis_configured():
        return 0
    from config.settings import get_settings
    from social_platform.database.session import session_scope

    stale_sec = max(300.0, float(get_settings().async_task_running_stale_seconds))
    now = schedule_now_utc_naive()
    cutoff = datetime.utcnow() - timedelta(seconds=stale_sec)
    reset = 0
    with session_scope() as db:
        rows = db.scalars(
            select(AsyncTask)
            .where(
                AsyncTask.status == "running",
                AsyncTask.cancel_requested.is_(False),
                AsyncTask.update_time < cutoff,
            )
            .order_by(AsyncTask.id.asc())
            .limit(batch_size)
        )
        for row in rows:
            if row is None:
                continue
            if normalize_schedule_datetime(row.task_start_time) > now:
                continue
            if normalize_schedule_datetime(row.task_end_time) <= now:
                continue
            tid = int(row.id)
            api_key = resolve_api_key_for_task(task_id=tid, row=row)
            if not api_key:
                continue
            get_redis().delete(_dispatch_lock_key(tid))
            row.status = "pending"
            row.celery_task_id = None
            row.update_time = datetime.utcnow()
            db.add(row)
            db.commit()
            cached = get_cached_async_task(tid)
            run_at = resolve_next_run_at(row, cached=cached, now=now)
            schedule_async_task_run(tid, run_at)
            update_async_task_cache(row, next_run_at=run_at)
            if is_run_at_due(run_at, now=now):
                dispatch_task_by_id(tid)
            reset += 1
    return reset


def recover_stale_pending_tasks(*, batch_size: int = 50) -> int:
    """
    补救：MySQL 中 pending、且可解析 api_key（Redis 或 MySQL）的任务重新入 ZSET；
    仅当 next_run_at（或窗口内首次时刻）已到期时才投递。
    """
    if not redis_configured():
        return 0
    from social_platform.database.session import session_scope

    now = schedule_now_utc_naive()
    recovered = 0
    with session_scope() as db:
        rows = db.scalars(
            select(AsyncTask)
            .where(
                AsyncTask.status == "pending",
                AsyncTask.cancel_requested.is_(False),
            )
            .order_by(AsyncTask.id.asc())
            .limit(batch_size)
        )
        for row in rows:
            if row is None:
                continue
            if normalize_schedule_datetime(row.task_start_time) > now:
                continue
            if normalize_schedule_datetime(row.task_end_time) <= now:
                continue
            tid = int(row.id)
            api_key = resolve_api_key_for_task(task_id=tid, row=row)
            if not api_key:
                continue
            cached = get_cached_async_task(tid)
            run_at = resolve_next_run_at(row, cached=cached, now=now)
            schedule_async_task_run(tid, run_at)
            update_async_task_cache(row, next_run_at=run_at)
            if not is_run_at_due(run_at, now=now):
                continue
            if _pending_already_queued(row):
                continue
            if dispatch_task_by_id(tid):
                recovered += 1
    return recovered


def _pending_already_queued(row: AsyncTask, *, grace_seconds: float = 600.0) -> bool:
    """
  pending 且已有 celery_task_id、近期未更新：视为 Celery 消息已在队列/执行中，
  避免 dispatch tick 重复 apply_async。
  """
    cid = (row.celery_task_id or "").strip()
    if not cid:
        return False
    updated = row.update_time or row.create_time
    if updated is None:
        return True
    u = updated.replace(tzinfo=None) if updated.tzinfo else updated
    age = (schedule_now_utc_naive() - u).total_seconds()
    return age < grace_seconds


def enqueue_async_task_execution(
    row: AsyncTask,
    *,
    api_key: str,
    run_at: datetime,
) -> Optional[str]:
    """
    提交/续期时写入 Redis 缓存并预约执行。

    - ``run_at`` 在未来：仅入 ZSET，由 HTTP 轮询 / Beat tick 到期投递（避免 countdown + ZSET 双投递）。
    - ``run_at`` 已到期：仅 ``apply_celery_run_at(countdown=0)``，并从 ZSET 移除，防止 Beat 再次投递。
    """
    target = normalize_schedule_datetime(run_at)
    key = (api_key or "").strip() or str(getattr(row, "api_key", "") or "").strip()
    if not key:
        logger.warning("skip enqueue async task %s: empty api_key", int(row.id))
        return None
    cache_async_task(row, api_key=key, next_run_at=target)
    now = schedule_now_utc_naive()
    tid = int(row.id)
    priority = int(row.priority or 0)

    if target > now:
        schedule_async_task_run(tid, target)
        return None

    cid = apply_celery_run_at(tid, key, target, priority=priority)
    if cid:
        unschedule_async_task(tid)
        return cid
    return dispatch_task_by_id(tid)


def restore_schedule_tasks_from_mysql(*, batch_size: int = 1000) -> dict[str, int]:
    """
    Worker 重启后恢复 Redis 调度：
    - 从 MySQL 扫描未取消、未完成且仍在窗口内的任务；
    - 如 Redis ZSET 不存在该 task_id，则补 zadd；
    - 避免重复恢复与重复注册。
    """
    if not redis_configured():
        logger.warning("skip restore schedule tasks: redis not configured")
        return {
            "restored": 0,
            "already_scheduled": 0,
            "skipped": 0,
            "skipped_no_api_key": 0,
            "dispatch_due_count": 0,
        }
    from social_platform.database.session import session_scope
    from config.settings import get_settings

    r = get_redis()
    if not r.set(RESTORE_LOCK_KEY, "1", nx=True, ex=120):
        logger.info("skip restore schedule tasks: another worker is restoring")
        return {
            "restored": 0,
            "already_scheduled": 0,
            "skipped": 0,
            "skipped_no_api_key": 0,
            "dispatch_due_count": 0,
        }
    now = schedule_now_utc_naive()
    restore_dispatch_due = bool(get_settings().async_restore_dispatch_due_on_startup)
    restored = 0
    already_scheduled = 0
    skipped = 0
    skipped_no_api_key = 0
    dispatch_due_count = 0
    try:
        with session_scope() as db:
            rows = db.scalars(
                select(AsyncTask)
                .where(
                    AsyncTask.cancel_requested.is_(False),
                    AsyncTask.status.in_(("pending", "running")),
                    AsyncTask.task_end_time > now,
                )
                .order_by(AsyncTask.id.asc())
                .limit(batch_size)
            )
            for row in rows:
                if row is None:
                    skipped += 1
                    continue
                tid = int(row.id)
                status = str(row.status or "")
                if status not in ("pending", "running"):
                    skipped += 1
                    _log_cleanup_schedule_member(tid, f"status_{status}")
                    continue
                if bool(getattr(row, "cancel_requested", False)):
                    skipped += 1
                    _log_cleanup_schedule_member(tid, "cancel_requested")
                    continue
                if normalize_schedule_datetime(row.task_end_time) <= now:
                    skipped += 1
                    continue
                api_key = resolve_api_key_for_task(task_id=tid, row=row)
                if not api_key:
                    skipped_no_api_key += 1
                    logger.warning("skip restore task without api_key: task_id=%s", tid)
                    continue
                cached = get_cached_async_task(tid)
                run_at = resolve_next_run_at(row, cached=cached, now=now)
                update_async_task_cache(
                    row,
                    next_run_at=run_at,
                    clear_next_run=(str(row.status or "") == "running"),
                )
                dispatch_now = restore_dispatch_due and is_run_at_due(run_at, now=now)
                logger.info(
                    "restore_schedule_task",
                    extra={
                        "task_id": int(tid),
                        "status": status,
                        "next_run_at": schedule_utc_iso(run_at),
                        "dispatch_immediately": bool(dispatch_now),
                    },
                )
                member = str(tid)
                if r.zscore(SCHEDULE_ZSET, member) is not None:
                    already_scheduled += 1
                else:
                    r.zadd(SCHEDULE_ZSET, {member: run_at.timestamp()})
                    logger.info("恢复定时任务: task_id=%s", tid)
                    restored += 1
                if dispatch_now and dispatch_task_by_id(tid):
                    dispatch_due_count += 1
    finally:
        r.delete(RESTORE_LOCK_KEY)
    return {
        "restored": restored,
        "already_scheduled": already_scheduled,
        "skipped": skipped,
        "skipped_no_api_key": skipped_no_api_key,
        "dispatch_due_count": dispatch_due_count,
    }
