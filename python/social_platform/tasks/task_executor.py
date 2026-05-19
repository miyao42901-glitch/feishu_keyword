from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from social_platform.actions.registry import get_action_spec
from social_platform.actions.runner import execute_public_action
from social_platform.api_response import from_worker_run
from social_platform.api_status_codes import CODE_SUCCESS
from social_platform.models.async_task import AsyncTask
from social_platform.services.search_persist import (
    SearchAllAsyncPersistState,
    apply_search_persist_stats_to_async_task,
    bind_search_all_async_persist,
    try_save_search_after_crawl,
    unbind_search_all_async_persist,
)
from social_platform.schedule_time import normalize_schedule_datetime
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


def execute_async_social_task(db: Session, task_id: int, api_key: str) -> None:
    """Celery worker：在 task_start～task_end 窗口内按 interval_minutes 周期执行采集。"""
    task = db.get(AsyncTask, task_id)
    if task is None:
        return
    resolved_api_key = (api_key or "").strip() or str(getattr(task, "api_key", "") or "").strip()
    if not resolved_api_key:
        logger.warning("async task %s missing api_key in payload and db", task_id)
        task.status = "failed"
        task.error_message = "missing api_key"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        return

    now = task_service.utc_now_naive()
    window_start = normalize_schedule_datetime(task.task_start_time)
    window_end = normalize_schedule_datetime(task.task_end_time)
    if task.cancel_requested:
        task.status = "cancelled"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        return
    if _async_search_all_should_bind_context(str(task.action or "")):
        max_fetch = task_service.normalize_fetch_count(task.fetch_count)
        success_done = max(0, int(task.success_count or 0))
        if success_done >= max_fetch:
            logger.info(
                "async task %s reached fetch_count: success_count=%s fetch_count=%s",
                task_id,
                success_done,
                max_fetch,
            )
            task.status = "success"
            task.update_time = datetime.utcnow()
            db.add(task)
            db.commit()
            return

    if now >= window_end:
        task.status = "success"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        return

    if now < window_start:
        task.status = "pending"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        async_task_redis.enqueue_async_task_execution(
            task, api_key=resolved_api_key, run_at=window_start
        )
        return

    if task.status == "running":
        from config.settings import get_settings

        stale_sec = max(300.0, float(get_settings().async_task_running_stale_seconds))
        updated = task.update_time or task.create_time
        if updated is not None:
            u = updated.replace(tzinfo=None) if updated.tzinfo else updated
            if (now - u).total_seconds() < stale_sec:
                return
        task.status = "pending"
        task.celery_task_id = None
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()

    task.status = "running"
    task.update_time = datetime.utcnow()
    db.add(task)
    db.commit()

    body = task_service.body_for_worker_execution(task)
    ok = False
    try:
        token: Any = None
        if _async_search_all_should_bind_context(str(task.action or "")):
            token = bind_search_all_async_persist(
                SearchAllAsyncPersistState(
                    db=db,
                    task_id=int(task_id),
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
        stats = try_save_search_after_crawl(
            task.action,
            body,
            raw,
            user_id=task.user_id,
            task_id=int(task_id),
        )
        if stats:
            apply_search_persist_stats_to_async_task(db, task_id, stats)

        api_body = from_worker_run(raw)
        ok = int(api_body.get("code", -1)) == CODE_SUCCESS

        task = db.get(AsyncTask, task_id)
        if task is None:
            return
        task.update_time = datetime.utcnow()
        if not ok:
            msg = api_body.get("msg")
            err = (str(msg) if msg is not None else "")[:64]
            task.error_message = err or None
        else:
            task.error_message = None
        db.add(task)
        db.commit()
        async_task_redis.update_async_task_cache(task, clear_next_run=True)
    except Exception:
        logger.exception("async task %s execution failed", task_id)
        task = db.get(AsyncTask, task_id)
        if task is None:
            return
        if not task.error_message:
            task.error_message = "execution error"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        async_task_redis.update_async_task_cache(task, clear_next_run=True)
        ok = False

    task_service.schedule_next_async_run(
        db,
        task_id,
        resolved_api_key,
        completed_at=task_service.utc_now_naive(),
        last_ok=ok,
    )
