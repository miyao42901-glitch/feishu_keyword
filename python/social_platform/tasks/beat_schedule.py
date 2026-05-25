"""Celery Beat 定时任务表；任务名须与 worker_tasks 中 @celery_app.task name 一致。"""

from __future__ import annotations

import logging
from typing import Any

from celery.schedules import crontab

TASK_ASYNC_SCHEDULE_DISPATCH = (
    "social_platform.tasks.worker_tasks.tick_async_schedule_dispatch"
)
TASK_JZL_SOCIAL = "social_platform.tasks.worker_tasks.run_jzl_social"
logger = logging.getLogger(__name__)


def build_async_dispatch_beat_schedule() -> dict[str, dict[str, Any]]:
    """从 Redis ZSET 扫描到期异步任务并投递 Celery Worker（与 HTTP 轮询逻辑一致）。"""
    from config.settings import get_settings

    settings = get_settings()
    if settings.async_dispatch_http_enabled:
        return {}
    if not settings.async_schedule_beat_enabled:
        return {}
    interval = max(15.0, float(settings.async_dispatch_poll_seconds))
    return {
        "beat-async-schedule-dispatch": {
            "task": TASK_ASYNC_SCHEDULE_DISPATCH,
            "schedule": interval,
            "options": {"expires": max(10, int(interval) - 1)},
        },
    }


def build_beat_schedule() -> dict[str, dict[str, Any]]:
    example_payload: dict[str, Any] = {
        "action": "douyin_search_page",
        "params": {
            "key": "",
            "keyword": "替换为你的词",
            "cursor": "",
            "logid": "",
        },
    }
    return {
        "beat-multi-social-example": {
            "task": TASK_JZL_SOCIAL,
            "schedule": crontab(minute="*/30"),
            "args": (example_payload,),
        },
    }
