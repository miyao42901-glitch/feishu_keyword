from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from social_platform.actions.registry import get_action_spec
from social_platform.actions.runner import execute_public_action
from social_platform.api_response import from_worker_run, worker_run_insufficient_balance
from social_platform.api_status_codes import CODE_SUCCESS
from social_platform.models.async_task import AsyncTask
from social_platform.services.search_persist import (
    SearchAllAsyncPersistState,
    apply_search_persist_stats_to_async_task,
    bind_search_all_async_persist,
    try_save_search_after_crawl,
    unbind_search_all_async_persist,
)
from social_platform.schedule_time import naive_dt, schedule_now_wall_naive
from social_platform.services import async_task_redis, task_service


_SEARCH_ALL_WORKER_ACTIONS = frozenset(
    {
        "douyin_search_all",
        "xhs_search_all",
        "wx_sousou_search_all",
        "mp_search_all",
    }
)


def _async_search_all_should_bind_context(public_action: str) -> bool:
    a = (public_action or "").strip()
    spec = get_action_spec(a)
    if spec and spec.worker_action in _SEARCH_ALL_WORKER_ACTIONS:
        return True
    return a.endswith("-search-all") or a in _SEARCH_ALL_WORKER_ACTIONS


def _lease_active(task: AsyncTask, *, now: datetime) -> bool:
    lease_until = task.running_lease_until
    if lease_until is None:
        return False
    if lease_until.tzinfo is not None:
        lease_until = lease_until.astimezone(timezone.utc).replace(tzinfo=None)
    return lease_until > now


def execute_async_social_task(db: Session, task_id: int, api_key: str) -> None:
    """Celery worker：执行当前轮；不写未来 next_run_at（由 schedule_next 负责）。"""
    task = db.get(AsyncTask, task_id)
    if task is None:
        return
    resolved_api_key = (api_key or "").strip() or str(getattr(task, "api_key", "") or "").strip()
    if not resolved_api_key:
        logger.warning("async task %s missing api_key in payload and db", task_id)
        task.status = "failed"
        task.error_message = "missing api_key"
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()
        return

    now = task_service.utc_now_naive()
    window_start = naive_dt(task.task_start_time)
    window_end = naive_dt(task.task_end_time)

    if task.cancel_requested:
        task.status = "cancelled"
        task.next_run_at = None
        task.current_run_id = None
        task.running_lease_until = None
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()
        async_task_redis.unschedule_async_task(task_id)
        return

    if now >= window_end:
        task.status = "success"
        task.next_run_at = None
        task.current_run_id = None
        task.running_lease_until = None
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()
        async_task_redis.unschedule_async_task(task_id)
        return

    if now < window_start:
        task.status = "pending"
        task.next_run_at = window_start
        task.current_run_id = None
        task.running_lease_until = None
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()
        async_task_redis.enqueue_async_task_execution(
            task, api_key=resolved_api_key, run_at=window_start
        )
        return

    if task.status == "running" and _lease_active(task, now=now):
        logger.info(
            "worker_skip_duplicate_running",
            extra={"task_id": int(task_id), "run_id": task.current_run_id},
        )
        return

    if task.status == "running" and not _lease_active(task, now=now):
        logger.warning(
            "worker_recover_expired_running",
            extra={"task_id": int(task_id), "run_id": task.current_run_id},
        )
        task.current_run_id = None
        task.running_lease_until = None
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()

    from config.settings import get_settings

    lease_seconds = max(120.0, float(get_settings().async_task_running_stale_seconds))
    run_id = str(uuid4())
    running_lease_until = now + timedelta(seconds=lease_seconds)

    task.status = "running"
    task.next_run_at = None
    task.current_run_id = run_id
    task.running_lease_until = running_lease_until
    task.update_time = schedule_now_wall_naive()
    db.add(task)
    db.commit()
    async_task_redis.unschedule_async_task(task_id)
    async_task_redis.update_async_task_cache(task, clear_next_run=True)
    logger.info(
        "async_task_run_started",
        extra={
            "task_id": int(task_id),
            "run_id": run_id,
            "running_lease_until": running_lease_until.isoformat(),
        },
    )

    body = task_service.body_for_worker_execution(task)
    ok = False
    try:
        token: Any = None
        if _async_search_all_should_bind_context(str(task.action or "")):
            token = bind_search_all_async_persist(
                SearchAllAsyncPersistState(
                    db=db,
                    task_id=int(task_id),
                    run_id=run_id,
                    user_id=str(task.user_id or ""),
                    public_action=str(task.action or ""),
                    body=body,
                )
            )
        try:
            raw = execute_public_action(task.action, body, resolved_api_key)
        except LookupError:
            raw = {
                "ok": False,
                "error": "unsupported action",
                "meta": None,
            }
        finally:
            if token is not None:
                unbind_search_all_async_persist(token)

        if worker_run_insufficient_balance(raw):
            task_service.cancel_async_task_on_insufficient_balance(
                db,
                user_id=str(task.user_id or ""),
                trigger_task_id=int(task_id),
            )
            return

        stats = try_save_search_after_crawl(
            task.action,
            body,
            raw,
            user_id=task.user_id,
            task_id=int(task_id),
        )
        if stats:
            apply_search_persist_stats_to_async_task(db, task_id, stats)
            db.commit()

        api_body = from_worker_run(raw)
        ok = int(api_body.get("code", -1)) == CODE_SUCCESS

        task = db.get(AsyncTask, task_id)
        if task is None:
            return
        task.update_time = schedule_now_wall_naive()
        if not ok:
            msg = api_body.get("msg")
            err = (str(msg) if msg is not None else "")[:64]
            task.error_message = err or None
        else:
            task.error_message = None
        db.add(task)
        db.commit()
    except Exception:
        logger.exception("async task %s execution failed", task_id)
        task = db.get(AsyncTask, task_id)
        if task is None:
            return
        if not task.error_message:
            task.error_message = "execution error"
        task.update_time = schedule_now_wall_naive()
        db.add(task)
        db.commit()
        ok = False

    task_service.schedule_next_async_run(
        db,
        task_id,
        resolved_api_key,
        completed_at=task_service.utc_now_naive(),
        last_ok=ok,
    )
