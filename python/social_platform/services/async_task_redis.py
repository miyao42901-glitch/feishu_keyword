"""异步任务 Redis 缓存 + ZSET 定时调度（HTTP 轮询 / Celery Beat / countdown 多路投递）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from social_platform.models.async_task import AsyncTask
from social_platform.redis_client import get_redis, redis_configured
from social_platform.schedule_time import (
    parse_schedule_utc_iso,
    parse_schedule_wall_clock,
    schedule_now_wall_naive,
    schedule_wall_clock_str,
    naive_dt,
    wall_clock_to_timestamp,
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

    end = naive_dt(task_end)
    now = schedule_now_wall_naive()
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


def _is_mysql_lock_wait_timeout(exc: BaseException) -> bool:
    if not isinstance(exc, OperationalError):
        return False
    parts = [str(exc)]
    orig = getattr(exc, "orig", None)
    if orig is not None:
        parts.append(str(orig))
    msg = " ".join(parts)
    return "1205" in msg or "Lock wait timeout exceeded" in msg


def _scheduler_skip_log(task_id: int, status: str, *, reason: str) -> None:
    logger.warning(
        "scheduler_skip task_id=%s status=%s reason=%s",
        int(task_id),
        status or "",
        reason,
    )


def _try_mark_pending_task_window_success(db: Session, row: AsyncTask) -> bool:
    """仅 pending 且采集窗口已结束时标 success；调用方负责 commit。"""
    tid = int(row.id)
    db.refresh(row)
    status = str(row.status or "")
    if status != "pending":
        _scheduler_skip_log(tid, status, reason="mark_success_not_pending")
        return False
    if naive_dt(row.task_end_time) > schedule_now_wall_naive():
        return False
    row.status = "success"
    row.next_run_at = None
    row.celery_task_id = None
    row.current_run_id = None
    row.running_lease_until = None
    row.update_time = schedule_now_wall_naive()
    db.add(row)
    return True


def _commit_or_skip_lock_timeout(db: Session, *, task_id: int, op: str) -> bool:
    """commit；遇 1205 则 rollback 并返回 False。"""
    try:
        db.commit()
        return True
    except OperationalError as e:
        db.rollback()
        if _is_mysql_lock_wait_timeout(e):
            logger.warning(
                "scheduler_lock_timeout task_id=%s op=%s",
                int(task_id),
                op,
            )
            return False
        raise


def parse_cached_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return naive_dt(value)
    if not isinstance(value, str):
        return None
    return parse_schedule_wall_clock(value)


def is_run_at_due(run_at: datetime, *, now: Optional[datetime] = None) -> bool:
    """判断 scheduled run_at 是否已到（东八区墙钟 naive）。"""
    t = naive_dt(now) if now is not None else schedule_now_wall_naive()
    at = naive_dt(run_at)
    return at <= t


def _lease_expired(row: AsyncTask, *, now: datetime) -> bool:
    lease_until = getattr(row, "running_lease_until", None)
    if lease_until is None:
        return True
    return naive_dt(lease_until) <= naive_dt(now)


def get_committed_next_run_at(row: AsyncTask) -> Optional[datetime]:
    """DB 中的 next_run_at（pending 等待 dispatch）；无 fallback。"""
    raw = getattr(row, "next_run_at", None)
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return naive_dt(raw)
    return parse_cached_datetime(raw)


def resolve_next_run_at(
    row: AsyncTask,
    *,
    cached: Optional[dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> datetime:
    """ZSET 对齐 / restore：优先 DB next_run_at，缺失时回退窗口内首次执行时刻。"""
    from social_platform.services.task_service import first_run_at

    t = now if now is not None else schedule_now_wall_naive()
    start = first_run_at(row, now=t)
    committed = get_committed_next_run_at(row)
    if committed is not None:
        return committed if committed >= start else start
    if cached:
        nxt = parse_cached_datetime(cached.get("next_run_at"))
        if nxt is not None:
            return nxt if nxt >= start else start
    return start


def _recovery_run_at(row: AsyncTask, *, now: Optional[datetime] = None) -> datetime:
    """running 租约过期后重新预约：按 interval_minutes 推迟，而非立即重跑。"""
    from social_platform.services.task_service import first_run_at, next_run_after_completion

    t = now if now is not None else schedule_now_wall_naive()
    nxt = next_run_after_completion(row, t)
    if nxt is not None:
        return nxt
    return first_run_at(row, now=t)


def _celery_broker_retry_seconds() -> int:
    """Celery broker 投递失败时的短退避（秒），与采集周期 interval 无关。"""
    return 60


def defer_pending_celery_dispatch(
    task_id: int,
    row: AsyncTask,
    *,
    reason: str,
) -> datetime:
    """Celery 投递失败时：将 next_run_at 推后并写回 ZSET，避免无间隔重复 dispatch。"""
    from social_platform.database.session import session_scope

    now = schedule_now_wall_naive()
    backoff = timedelta(seconds=_celery_broker_retry_seconds())
    deferred = now + backoff
    committed = get_committed_next_run_at(row)
    # 仅保留「未来」的采集预约（如 schedule_next 写入）；勿把已过期或首次调度时刻顶掉短退避
    if committed is not None and committed > now and committed > deferred:
        deferred = committed
    end = naive_dt(row.task_end_time)
    if deferred >= end:
        unschedule_async_task(task_id)
        return deferred
    tid = int(task_id)
    with session_scope() as db:
        db_row = db.get(AsyncTask, tid)
        if db_row is not None and str(db_row.status or "") == "pending":
            db_row.next_run_at = deferred
            db_row.update_time = schedule_now_wall_naive()
            db.add(db_row)
            row = db_row
    schedule_async_task_run(tid, deferred)
    update_async_task_cache(row, next_run_at=deferred)
    logger.warning(
        "celery_dispatch_deferred",
        extra={
            "task_id": tid,
            "reason": str(reason),
            "next_run_at": schedule_wall_clock_str(deferred),
            "backoff_seconds": int(backoff.total_seconds()),
        },
    )
    return deferred


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
            schedule_wall_clock_str(row.task_start_time)
            if row.task_start_time
            else None
        ),
        "task_end_time": (
            schedule_wall_clock_str(row.task_end_time)
            if row.task_end_time
            else None
        ),
        "interval_minutes": interval_min,
        "interval_seconds": interval_minutes_to_seconds(interval_min),
        "fetch_count": int(getattr(row, "fetch_count", None) or 100),
        "run_id": str(getattr(row, "current_run_id", "") or ""),
        "running_lease_until": (
            schedule_wall_clock_str(row.running_lease_until)
            if getattr(row, "running_lease_until", None) is not None
            else None
        ),
    }
    if clear_next_run:
        return payload
    if next_run_at is not None:
        payload["next_run_at"] = schedule_wall_clock_str(next_run_at)
    elif getattr(row, "next_run_at", None) is not None:
        payload["next_run_at"] = schedule_wall_clock_str(row.next_run_at)
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
    score = wall_clock_to_timestamp(run_at)
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
    """通过 Celery countdown 投递 worker；返回 Celery task id。"""
    from social_platform.tasks.worker_tasks import run_social_async_task

    key = (api_key or "").strip()
    if not key:
        return None
    now = schedule_now_wall_naive()
    target = naive_dt(run_at)
    countdown = max(0, int((target - now).total_seconds()))
    kwargs: dict[str, Any] = {
        "args": [int(task_id), key],
        "priority": int(priority),
    }
    if countdown > 0:
        kwargs["countdown"] = countdown
    try:
        async_result = run_social_async_task.apply_async(**kwargs)
    except Exception as exc:
        broker_errors: tuple[type[BaseException], ...]
        try:
            from kombu.exceptions import OperationalError as KombuOperationalError

            broker_errors = (KombuOperationalError, ConnectionError, OSError)
        except ImportError:
            broker_errors = (ConnectionError, OSError)
        if not isinstance(exc, broker_errors):
            raise
        logger.warning(
            "celery_apply_async_failed task_id=%s: %s",
            int(task_id),
            exc,
        )
        return None
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
            row.update_time = schedule_now_wall_naive()
            db.add(row)
    update_cached_celery_id(task_id, celery_task_id)


def dispatch_task_by_id(task_id: int) -> Optional[str]:
    """pending 且 next_run_at<=now 时投递 Celery；running 有效租约时跳过。"""
    if not redis_configured():
        return None
    r = get_redis()
    lock_key = _dispatch_lock_key(task_id)
    lock_ttl = _dispatch_lock_ttl_seconds()
    if not r.set(lock_key, "1", nx=True, ex=lock_ttl):
        ttl = int(r.ttl(lock_key) or -2)
        if ttl <= 0:
            r.delete(lock_key)
            if not r.set(lock_key, "1", nx=True, ex=lock_ttl):
                return None
        else:
            return None

    from social_platform.database.session import session_scope

    try:
        priority = 0
        api_key: Optional[str] = None
        now = schedule_now_wall_naive()
        with session_scope() as db:
            row = db.get(AsyncTask, int(task_id))
            if row is None:
                unschedule_async_task(task_id)
                _log_cleanup_schedule_member(task_id, "task_not_found")
                return None
            status = str(row.status or "")
            if row.cancel_requested or status in ("cancelled", "success", "failed"):
                unschedule_async_task(task_id)
                _log_cleanup_schedule_member(task_id, f"status_{status}")
                return None
            if now >= naive_dt(row.task_end_time):
                if not _try_mark_pending_task_window_success(db, row):
                    return None
                if not _commit_or_skip_lock_timeout(
                    db, task_id=task_id, op="dispatch_mark_success"
                ):
                    return None
                unschedule_async_task(task_id)
                _log_cleanup_schedule_member(task_id, "task_window_ended")
                return None
            if status == "running":
                if not _lease_expired(row, now=now):
                    return None
                return None
            if status != "pending":
                return None
            committed = get_committed_next_run_at(row)
            if committed is None:
                return None
            if not is_run_at_due(committed, now=now):
                schedule_async_task_run(task_id, committed)
                update_async_task_cache(row, next_run_at=committed)
                return None
            if _pending_celery_in_flight(row):
                return None
            api_key = resolve_api_key_for_task(task_id=task_id, row=row)
            if not api_key:
                logger.warning("async task %s missing api_key in redis and mysql", task_id)
                return None
            priority = int(row.priority or 0)

        run_at = committed if committed is not None else schedule_now_wall_naive()
        cid = apply_celery_run_at(
            task_id, str(api_key or ""), run_at, priority=priority
        )
        if cid:
            unschedule_async_task(task_id)
            return cid
        with session_scope() as db:
            row = db.get(AsyncTask, int(task_id))
            if row is not None and str(row.status or "") == "pending":
                defer_pending_celery_dispatch(
                    task_id, row, reason="apply_async_failed"
                )
        return None
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
    now_dt = schedule_now_wall_naive()
    now = wall_clock_to_timestamp(now_dt)
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
                    elif now >= wall_clock_to_timestamp(row.task_end_time):
                        should_cleanup = True
                        cleanup_reason = "task_window_ended"
            if should_cleanup:
                _log_cleanup_schedule_member(tid, cleanup_reason)
                continue
            defer_dt = now_dt + timedelta(seconds=30)
            with session_scope() as db:
                row = db.get(AsyncTask, int(tid))
                if row is not None:
                    committed = get_committed_next_run_at(row)
                    if (
                        str(row.status or "") == "pending"
                        and committed is not None
                    ):
                        if committed > defer_dt:
                            defer_dt = committed
                        schedule_async_task_run(tid, defer_dt)
                        logger.info(
                            "async task %s dispatch deferred, re-queued at %s",
                            tid,
                            defer_dt,
                        )
                        continue
            r.zadd(SCHEDULE_ZSET, {member: wall_clock_to_timestamp(defer_dt)})
            logger.info(
                "async task %s dispatch deferred, re-queued at %s", tid, defer_dt
            )
    return dispatched


def _pending_celery_in_flight(row: AsyncTask, *, grace_seconds: float = 120.0) -> bool:
    """
    pending 且近期已投递 Celery：避免重复 apply_async。
    仅当 next_run_at 仍未到期时生效；已到期须允许再次 dispatch（上一轮 Celery 通常已结束）。
    """
    if str(row.status or "") != "pending":
        return False
    cid = (row.celery_task_id or "").strip()
    if not cid:
        return False
    committed = get_committed_next_run_at(row)
    now = schedule_now_wall_naive()
    if committed is not None and is_run_at_due(committed, now=now):
        return False
    updated = row.update_time or row.create_time
    if updated is None:
        return True
    u = updated.replace(tzinfo=None) if updated.tzinfo else updated
    age = (now - u).total_seconds()
    return age < grace_seconds


def recover_stale_running_tasks(*, batch_size: int = 50) -> int:
    """running 租约过期：重置为 pending 并写入 next_run_at（DB 真源）+ ZSET。"""
    if not redis_configured():
        return 0
    from social_platform.database.session import session_scope

    now = schedule_now_wall_naive()
    reset = 0
    with session_scope() as db:
        rows = list(
            db.scalars(
                select(AsyncTask)
                .where(
                    AsyncTask.status == "running",
                    AsyncTask.cancel_requested.is_(False),
                    or_(
                        AsyncTask.running_lease_until.is_(None),
                        AsyncTask.running_lease_until < now,
                    ),
                )
                .order_by(AsyncTask.id.asc())
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
        )
        for row in rows:
            if row is None:
                continue
            tid = int(row.id)
            try:
                if naive_dt(row.task_start_time) > now:
                    continue
                if naive_dt(row.task_end_time) <= now:
                    continue
                db.refresh(row)
                if str(row.status or "") != "running":
                    _scheduler_skip_log(
                        tid,
                        str(row.status or ""),
                        reason="reset_running_status_changed",
                    )
                    continue
                api_key = resolve_api_key_for_task(task_id=tid, row=row)
                if not api_key:
                    continue
                get_redis().delete(_dispatch_lock_key(tid))
                run_at = _recovery_run_at(row, now=now)
                row.status = "pending"
                row.next_run_at = run_at
                row.celery_task_id = None
                row.current_run_id = None
                row.running_lease_until = None
                row.update_time = schedule_now_wall_naive()
                db.add(row)
                if not _commit_or_skip_lock_timeout(
                    db, task_id=tid, op="recover_reset_running"
                ):
                    continue
                schedule_async_task_run(tid, run_at)
                update_async_task_cache(row, next_run_at=run_at)
                reset += 1
            except OperationalError as e:
                db.rollback()
                if _is_mysql_lock_wait_timeout(e):
                    logger.warning(
                        "scheduler_lock_timeout task_id=%s status=%s op=recover_stale_running",
                        tid,
                        str(row.status or ""),
                    )
                    continue
                raise
    return reset


def recover_stale_pending_tasks(*, batch_size: int = 50) -> int:
    """pending 且 DB 有 next_run_at：对齐 ZSET；到期则 dispatch。"""
    if not redis_configured():
        return 0
    from social_platform.database.session import session_scope

    now = schedule_now_wall_naive()
    recovered = 0
    with session_scope() as db:
        rows = list(
            db.scalars(
                select(AsyncTask)
                .where(
                    AsyncTask.status == "pending",
                    AsyncTask.cancel_requested.is_(False),
                    AsyncTask.next_run_at.is_not(None),
                )
                .order_by(AsyncTask.id.asc())
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
        )
        for row in rows:
            if row is None:
                continue
            tid = int(row.id)
            try:
                end = naive_dt(row.task_end_time)
                if end <= now:
                    if not _try_mark_pending_task_window_success(db, row):
                        continue
                    if not _commit_or_skip_lock_timeout(
                        db, task_id=tid, op="recover_mark_success"
                    ):
                        continue
                    unschedule_async_task(tid)
                    continue
                db.refresh(row)
                if str(row.status or "") != "pending":
                    _scheduler_skip_log(
                        tid,
                        str(row.status or ""),
                        reason="recover_dispatch_not_pending",
                    )
                    continue
                api_key = resolve_api_key_for_task(task_id=tid, row=row)
                if not api_key:
                    continue
                committed = get_committed_next_run_at(row)
                if committed is None:
                    continue
                # 始终对齐 ZSET（窗口开始前也需写入，避免仅依赖首次 enqueue 时 ZSET 丢失）
                schedule_async_task_run(tid, committed)
                update_async_task_cache(row, next_run_at=committed)
                if naive_dt(row.task_start_time) > now:
                    continue
                if not is_run_at_due(committed, now=now):
                    continue
                if _pending_celery_in_flight(row):
                    continue
                if dispatch_task_by_id(tid):
                    recovered += 1
            except OperationalError as e:
                db.rollback()
                if _is_mysql_lock_wait_timeout(e):
                    logger.warning(
                        "scheduler_lock_timeout task_id=%s status=%s op=recover_stale_pending",
                        tid,
                        str(row.status or ""),
                    )
                    continue
                raise
    return recovered


def enqueue_async_task_execution(
    row: AsyncTask,
    *,
    api_key: str,
    run_at: datetime,
) -> Optional[str]:
    """
    同步 Redis 缓存与 ZSET；run_at 在未来仅 zadd，已到期则 dispatch。
    调用方（submit / schedule_next）须已把 next_run_at 写入 DB。
    """
    target = naive_dt(run_at)
    key = (api_key or "").strip() or str(getattr(row, "api_key", "") or "").strip()
    if not key:
        logger.warning("skip enqueue async task %s: empty api_key", int(row.id))
        return None
    cache_async_task(row, api_key=key, next_run_at=target)
    tid = int(row.id)
    now = schedule_now_wall_naive()

    if target > now:
        schedule_async_task_run(tid, target)
        return None

    cid = dispatch_task_by_id(tid)
    if cid:
        return cid
    return apply_celery_run_at(tid, key, target, priority=int(row.priority or 0))


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
    now = schedule_now_wall_naive()
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
                if status == "running":
                    skipped += 1
                    continue
                if status != "pending":
                    skipped += 1
                    _log_cleanup_schedule_member(tid, f"status_{status}")
                    continue
                if bool(getattr(row, "cancel_requested", False)):
                    skipped += 1
                    _log_cleanup_schedule_member(tid, "cancel_requested")
                    continue
                if naive_dt(row.task_end_time) <= now:
                    skipped += 1
                    continue
                committed = get_committed_next_run_at(row)
                if committed is None:
                    cached = get_cached_async_task(tid)
                    committed = resolve_next_run_at(row, cached=cached, now=now)
                api_key = resolve_api_key_for_task(task_id=tid, row=row)
                if not api_key:
                    skipped_no_api_key += 1
                    logger.warning("skip restore task without api_key: task_id=%s", tid)
                    continue
                update_async_task_cache(row, next_run_at=committed)
                dispatch_now = restore_dispatch_due and is_run_at_due(committed, now=now)
                logger.info(
                    "restore_schedule_task",
                    extra={
                        "task_id": int(tid),
                        "status": status,
                        "next_run_at": schedule_wall_clock_str(committed),
                        "dispatch_immediately": bool(dispatch_now),
                    },
                )
                member = str(tid)
                old_score = r.zscore(SCHEDULE_ZSET, member)
                r.zadd(SCHEDULE_ZSET, {member: wall_clock_to_timestamp(committed)})
                if old_score is not None and float(old_score) == float(
                    wall_clock_to_timestamp(committed)
                ):
                    already_scheduled += 1
                else:
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
