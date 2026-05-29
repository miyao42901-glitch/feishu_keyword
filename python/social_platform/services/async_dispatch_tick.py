"""异步任务调度统一 tick：HTTP 后台线程与 Celery Beat 共用。"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
