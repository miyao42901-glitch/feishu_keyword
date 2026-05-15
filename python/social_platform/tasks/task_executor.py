from __future__ import annotations

from datetime import datetime
from typing import Any

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


def _async_search_all_should_bind_context(public_action: str) -> bool:
    a = (public_action or "").strip()
    spec = get_action_spec(a)
    if spec and spec.worker_action in ("douyin_search_all", "xhs_search_all"):
        return True
    return a in ("douyin_search_all", "xhs_search_all")


def execute_async_social_task(db: Session, task_id: int, api_key: str) -> None:
    """Celery worker：按注册 action 执行聚合任务 → 统一落库与任务状态。"""
    task = db.get(AsyncTask, task_id)
    if task is None:
        return
    if task.cancel_requested:
        task.status = "cancelled"
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        return

    task.status = "running"
    task.update_time = datetime.utcnow()
    db.add(task)
    db.commit()

    body = dict(task.body_json or {})
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
        raw = execute_public_action(task.action, body, api_key)
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
    if ok:
        task.status = "success"
        task.error_message = None
    else:
        task.status = "failed"
        msg = api_body.get("msg")
        err = (str(msg) if msg is not None else "")[:64]
        task.error_message = err or None
    db.add(task)
    db.commit()
