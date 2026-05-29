"""Celery broker 校验、启动探活、worker 在线检测、safe_apply_async。"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from config.settings import Settings, get_settings
from social_platform.celery_env import log_celery_broker_env

logger = logging.getLogger(__name__)


class CeleryBrokerConfigError(RuntimeError):
    """Broker/backend 未配置或使用了不允许的协议。"""


class CeleryWorkerOfflineError(RuntimeError):
    """无 Celery worker 响应 control.ping。"""


def require_redis_celery_url(url: str, env_name: str) -> str:
    """校验必须为显式配置的 redis:// / rediss://，禁止 amqp 与 silent fallback。"""
    value = (url or "").strip()
    if not value:
        raise CeleryBrokerConfigError(f"{env_name} 未配置")
    lower = value.lower()
    if lower.startswith("amqp://") or lower.startswith("amqps://"):
        raise CeleryBrokerConfigError(
            f"{env_name} 不允许使用 RabbitMQ (amqp)：当前值={value!r}，请改为 redis://"
        )
    if not (lower.startswith("redis://") or lower.startswith("rediss://")):
        raise CeleryBrokerConfigError(
            f"{env_name} 必须为 redis:// 或 rediss://，当前值={value!r}"
        )
    return value


def resolve_broker_and_backend(settings: Settings) -> tuple[str, str]:
    broker = require_redis_celery_url(
        settings.celery_broker_url, "CELERY_BROKER_URL"
    )
    backend = require_redis_celery_url(
        settings.celery_result_backend, "CELERY_RESULT_BACKEND"
    )
    return broker, backend


def _broker_error_types() -> tuple[type[BaseException], ...]:
    try:
        from kombu.exceptions import OperationalError as KombuOperationalError

        return (KombuOperationalError, ConnectionError, OSError)
    except ImportError:
        return (ConnectionError, OSError)


def celery_workers_online(*, timeout: float = 1.0) -> bool:
    """通过 control.ping 检测是否有 worker 在线。"""
    settings = get_settings()
    if settings.celery_task_eager:
        return True
    from social_platform.tasks.celery_app import celery_app

    try:
        inspect = celery_app.control.inspect(timeout=timeout)
        if inspect is None:
            return False
        ping = inspect.ping()
        return bool(ping)
    except Exception:
        logger.exception("celery control.ping failed")
        return False


def ensure_celery_startup_health(log: Optional[logging.Logger] = None) -> None:
    """
    FastAPI 启动阶段：打印环境来源、校验 broker/backend、探活 broker 与 Redis。
    失败则抛出异常，阻止服务在 broker 不可用时继续运行。
    """
    log = log or logger
    settings = get_settings()
    log_celery_broker_env(log)

    broker, backend = resolve_broker_and_backend(settings)
    log.warning("Celery broker=%s", broker)
    log.warning("Celery backend=%s", backend)

    if settings.celery_task_eager:
        log.warning(
            "CELERY_TASK_ALWAYS_EAGER=1，跳过 broker ensure_connection 与 worker ping"
        )
        return

    from social_platform.redis_client import ping_redis
    from social_platform.tasks.celery_app import celery_app

    if not ping_redis():
        raise RuntimeError(
            f"REDIS_URL 不可用，ping 失败: {settings.redis_url!r}"
        )
    log.warning("Redis ping OK: %s", settings.redis_url)

    try:
        with celery_app.connection_or_acquire() as conn:
            conn.ensure_connection(max_retries=3)
    except Exception as exc:
        log.exception(
            "Celery broker ensure_connection 失败 broker=%s backend=%s",
            broker,
            backend,
        )
        raise RuntimeError(
            f"Celery broker 不可用: {broker!r} ({type(exc).__name__}: {exc})"
        ) from exc
    log.warning("Celery broker ensure_connection OK")

    if settings.celery_require_worker_online and not celery_workers_online():
        log.error("Celery worker offline（启动阶段仅告警；派发阶段将阻止 apply_async）")


def safe_apply_async(
    task: Any,
    *,
    task_id: Optional[int] = None,
    apply_kwargs: Optional[dict[str, Any]] = None,
    max_retries: Optional[int] = None,
    backoff_base: Optional[float] = None,
) -> Any:
    """
    带指数退避的 apply_async；记录 broker/queue/routing_key/countdown/task_name。
    重试耗尽后重新抛出最后一次异常（不静默吞掉）。
    """
    settings = get_settings()
    kwargs = dict(apply_kwargs or {})
    retries = max_retries if max_retries is not None else settings.celery_apply_async_max_retries
    base = (
        backoff_base
        if backoff_base is not None
        else settings.celery_apply_async_backoff_base
    )
    broker = resolve_broker_and_backend(settings)[0]
    task_name = getattr(task, "name", repr(task))
    queue = kwargs.get("queue")
    routing_key = kwargs.get("routing_key")
    countdown = kwargs.get("countdown")
    broker_errors = _broker_error_types()

    if not settings.celery_task_eager and settings.celery_require_worker_online:
        if not celery_workers_online():
            logger.error(
                "Celery worker offline, block dispatch task_name=%s task_id=%s broker=%s",
                task_name,
                task_id,
                broker,
            )
            raise CeleryWorkerOfflineError(
                f"Celery worker offline, cannot dispatch {task_name}"
            )

    last_exc: Optional[BaseException] = None
    for attempt in range(max(1, int(retries))):
        try:
            return task.apply_async(**kwargs)
        except CeleryWorkerOfflineError:
            raise
        except Exception as exc:
            last_exc = exc
            logger.exception(
                "safe_apply_async failed attempt=%s/%s task_name=%s task_id=%s "
                "broker=%s queue=%s routing_key=%s countdown=%s apply_kwargs=%s",
                attempt + 1,
                retries,
                task_name,
                task_id,
                broker,
                queue,
                routing_key,
                countdown,
                kwargs,
            )
            if not isinstance(exc, broker_errors):
                raise
            if attempt + 1 >= retries:
                break
            delay = float(base) * (2**attempt)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc
