"""Celery 应用：broker/backend 与任务注册（供 `celery -A celery_jobs.celery_app` 或本模块启动）。"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Windows：billiard 默认 prefork 易触发 ``fast_trace_task`` 中 ``_loc`` 解包失败（celery/celery#8921）。
# 须在导入 Celery / billiard 之前设置；另见下方 ``worker_pool = "solo"``。
if sys.platform == "win32":
    os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")

_PY = Path(__file__).resolve().parent.parent.parent
_roots = {str(Path(p).resolve()) for p in sys.path if isinstance(p, str) and p}
for p in (_PY, _PY / "workers"):
    s = str(p.resolve())
    if s not in _roots:
        sys.path.insert(0, s)
        _roots.add(s)

from social_platform.env_bootstrap import ensure_dotenv_loaded

ensure_dotenv_loaded()

from celery import Celery
from celery.signals import worker_ready

from config.settings import get_settings

_settings = get_settings()
logger = logging.getLogger(__name__)

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

if sys.platform == "win32":
    celery_app.conf.worker_pool = "solo"

celery_app.conf.include = ["social_platform.tasks.worker_tasks"]

# 未来：多队列 / 优先级路由可在此扩展 task_routes、task_queues
# celery_app.conf.task_routes = {...}

_beat: dict[str, dict] = {}
if _settings.async_schedule_beat_enabled:
    from social_platform.tasks.beat_schedule import build_async_dispatch_beat_schedule

    _beat.update(build_async_dispatch_beat_schedule())
if _settings.celery_beat_enabled:
    from social_platform.tasks.beat_schedule import build_beat_schedule

    _beat.update(build_beat_schedule())
if _beat:
    celery_app.conf.beat_schedule = _beat


@worker_ready.connect
def restore_schedule_tasks(**kwargs: object) -> None:
    """Celery worker 启动后恢复 Redis 定时调度队列。"""
    from social_platform.services import async_task_redis

    try:
        stats = async_task_redis.restore_schedule_tasks_from_mysql()
        logger.info(
            "async schedule restore finished restored=%s already_scheduled=%s skipped=%s skipped_no_api_key=%s dispatch_due_count=%s",
            int(stats.get("restored", 0)),
            int(stats.get("already_scheduled", 0)),
            int(stats.get("skipped", 0)),
            int(stats.get("skipped_no_api_key", 0)),
            int(stats.get("dispatch_due_count", 0)),
        )
    except Exception:
        logger.exception("restore schedule tasks failed on worker_ready")
