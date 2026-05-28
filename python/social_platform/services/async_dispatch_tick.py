"""异步任务调度统一 tick：HTTP 后台线程、Celery Beat 与列表 API 补偿共用。"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_API_DISPATCH_COALESCE_KEY = "feishu:async:dispatch_tick:api_coalesce"


@dataclass(frozen=True)
class AsyncDispatchTickResult:
    dispatched: int = 0
    recovered_pending: int = 0
    reset_running: int = 0

    @property
    def total_actions(self) -> int:
        return self.dispatched + self.recovered_pending + self.reset_running


def run_async_dispatch_tick() -> AsyncDispatchTickResult:
    """
    扫描 Redis ZSET 投递到期任务，并补救 MySQL 中 pending / 超时 running 任务。
    返回本轮统计（便于 Beat 任务记录结果）。
    """
    from social_platform.services import async_task_redis

    dispatched = async_task_redis.dispatch_due_async_tasks()
    reset_running = async_task_redis.recover_stale_running_tasks()
    recovered_pending = async_task_redis.recover_stale_pending_tasks()

    result = AsyncDispatchTickResult(
        dispatched=dispatched,
        recovered_pending=recovered_pending,
        reset_running=reset_running,
    )
    logger.info(
        "async_dispatch_tick",
        extra={
            "dispatch_due_count": int(dispatched),
            "restore_count": int(recovered_pending),
            "reset_running_count": int(reset_running),
            "total_actions": int(result.total_actions),
        },
    )
    return result


def try_coalesced_dispatch_tick_from_api() -> None:
    """
    读接口（如 GET /async/tasks）触发的调度补偿：与后台轮询共用 tick，Redis 节流。
    列表轮询不能替代调度，但在 HTTP 后台线程未跑或 ZSET 丢失时可尽快投递到期任务。
    """
    from config.settings import get_settings
    from social_platform.redis_client import redis_configured
    from social_platform.services.task_service import redis_ready

    settings = get_settings()
    if not settings.database_url.strip():
        return
    if not redis_configured() or not redis_ready():
        return

    from social_platform.redis_client import get_redis

    interval = max(5.0, float(settings.async_dispatch_poll_seconds))
    ttl = max(5, int(interval * 0.9))
    if not get_redis().set(_API_DISPATCH_COALESCE_KEY, "1", nx=True, ex=ttl):
        return
    try:
        run_async_dispatch_tick()
    except Exception:
        logger.exception("coalesced async dispatch tick from api failed")
