"""HTTP 进程内异步任务调度轮询（无需单独启动 Celery Beat）。"""

from __future__ import annotations

import logging
import threading
import time

from config.settings import get_settings

logger = logging.getLogger(__name__)

_loop_started = False
_loop_lock = threading.Lock()


def _dispatch_tick() -> None:
    from social_platform.services.async_dispatch_tick import run_async_dispatch_tick

    run_async_dispatch_tick()


def start_async_dispatch_loop() -> None:
    """在 HTTP 启动时开启后台线程，扫描 Redis ZSET 并补救 pending 任务。"""
    global _loop_started
    settings = get_settings()
    if settings.async_dispatch_http_enabled and settings.async_schedule_beat_enabled:
        logger.warning(
            "dual_dispatch_warning",
            extra={
                "dispatch_mode": "http+beat",
                "duplicate_dispatch_risk": True,
                "dual_dispatch_warning": 1,
            },
        )
    if not settings.async_dispatch_http_enabled:
        return
    if not settings.database_url.strip():
        return

    from social_platform.services.task_service import redis_ready

    if not redis_ready():
        logger.warning("async dispatch loop skipped: redis not ready")
        return

    with _loop_lock:
        if _loop_started:
            return
        _loop_started = True

    try:
        _dispatch_tick()
    except Exception:
        logger.exception("async dispatch initial tick failed")

    interval = max(5.0, float(settings.async_dispatch_poll_seconds))

    def _loop() -> None:
        while True:
            time.sleep(interval)
            try:
                _dispatch_tick()
            except Exception:
                logger.exception("async dispatch tick failed")

    threading.Thread(
        target=_loop,
        name="feishu-async-dispatch",
        daemon=True,
    ).start()
    logger.info("async dispatch loop started (interval=%ss)", interval)
