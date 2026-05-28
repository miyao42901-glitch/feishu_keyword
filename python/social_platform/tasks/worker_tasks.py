"""Celery 任务入口（HTTP 异步任务 + Beat 聚合任务）。"""

from __future__ import annotations

from typing import Any

from social_platform.tasks.celery_app import celery_app

TASK_JZL_SOCIAL = "social_platform.tasks.worker_tasks.run_jzl_social"
TASK_SOCIAL_ASYNC = "social_platform.tasks.worker_tasks.run_social_async_task"
TASK_ASYNC_SCHEDULE_DISPATCH = (
    "social_platform.tasks.worker_tasks.tick_async_schedule_dispatch"
)


@celery_app.task(name=TASK_JZL_SOCIAL)
def run_jzl_social(payload: dict[str, Any]) -> dict[str, Any]:
    from social_platform.aggregated_job import run_task

    return run_task(payload)


@celery_app.task(name=TASK_SOCIAL_ASYNC)
def run_social_async_task(task_id: int | str, api_key: str = "") -> None:
    from social_platform.database.session import session_scope
    from social_platform.tasks.task_executor import execute_async_social_task

    tid = int(task_id)
    with session_scope() as db:
        execute_async_social_task(db, tid, api_key)


@celery_app.task(name=TASK_ASYNC_SCHEDULE_DISPATCH)
def tick_async_schedule_dispatch() -> dict[str, int]:
    from social_platform.services.async_dispatch_tick import run_async_dispatch_tick

    r = run_async_dispatch_tick()
    return {
        "dispatched": r.dispatched,
        "recovered_pending": r.recovered_pending,
        "reset_running": r.reset_running,
    }
