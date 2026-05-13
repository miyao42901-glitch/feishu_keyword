"""Celery 应用：broker/backend 来自 config.Settings（python/.env）。"""
from __future__ import annotations

import sys
from pathlib import Path

_PY = Path(__file__).resolve().parent.parent
for p in (_PY, _PY / "workers"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from celery import Celery

from config.settings import get_settings

_settings = get_settings()

celery_app = Celery(
    "feishu_keyword",
    broker=_settings.resolved_celery_broker(),
    backend=_settings.resolved_celery_backend(),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=_settings.celery_task_eager,
    task_eager_propagates=_settings.celery_task_eager,
)

celery_app.conf.include = ["celery_jobs.tasks.social_task"]

if _settings.celery_beat_enabled:
    from celery_jobs import schedules

    celery_app.conf.beat_schedule = schedules.build_beat_schedule()
