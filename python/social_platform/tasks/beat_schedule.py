"""Celery Beat 定时任务表（示例）；任务名须与 worker_tasks 中 @celery_app.task name 一致。"""
from __future__ import annotations

from typing import Any

from celery.schedules import crontab

from social_platform.tasks.worker_tasks import TASK_JZL_SOCIAL


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
