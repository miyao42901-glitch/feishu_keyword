"""Celery Beat 定时任务：在 python/.env 设置 CELERY_BEAT_ENABLED=1 时由 celery_app 加载。

修改下方 payload 为你的业务信封；任务名须与 tasks.social_task 中 @shared_task name 一致。
"""
from __future__ import annotations

from typing import Any

from celery.schedules import crontab

# 与 celery_jobs.tasks.social_task.run_jzl_social 上 @celery_app.task(name=...) 保持一致
TASK_JZL_SOCIAL = "celery_jobs.tasks.social_task.run_jzl_social"


def build_beat_schedule() -> dict[str, dict[str, Any]]:
    # 示例：每 30 分钟拉一次（请按业务改 action/params）
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
