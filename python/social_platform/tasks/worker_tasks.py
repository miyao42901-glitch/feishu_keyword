"""Celery 任务入口（HTTP 异步任务 + 兼容旧 Beat 任务名）。"""
from __future__ import annotations

from typing import Any

from social_platform.tasks.celery_app import celery_app

# 与历史 celery_jobs.tasks.social_task 及 Beat 配置保持一致
TASK_JZL_SOCIAL = "celery_jobs.tasks.social_task.run_jzl_social"
TASK_SOCIAL_ASYNC = "social_platform.tasks.worker_tasks.run_social_async_task"


@celery_app.task(name=TASK_JZL_SOCIAL)
def run_jzl_social(payload: dict[str, Any]) -> dict[str, Any]:
    from social_platform.aggregated_job import run_task

    return run_task(payload)


@celery_app.task(name=TASK_SOCIAL_ASYNC)
def run_social_async_task(task_id: int | str, api_key: str) -> None:
    from social_platform.database.session import session_scope
    from social_platform.tasks.task_executor import execute_async_social_task

    tid = int(task_id)
    with session_scope() as db:
        execute_async_social_task(db, tid, api_key)
