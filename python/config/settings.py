"""集中配置：从环境变量与 python 目录下 .env 读取。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# python/config/settings.py -> 环境变量在仓库根 .env、.env.local
_PY_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _PY_ROOT.parent


def _settings_env_files() -> tuple[str, ...]:
    files: list[str] = []
    env_path = _REPO_ROOT / ".env"
    if env_path.is_file():
        files.append(str(env_path))
    local_path = _REPO_ROOT / ".env.local"
    if local_path.is_file():
        files.append(str(local_path))
    return tuple(files) if files else (str(env_path),)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_settings_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Celery / Redis
    redis_url: str = Field(
        default="redis://127.0.0.1:6379/0", validation_alias="REDIS_URL"
    )
    celery_broker_url: str = Field(default="", validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default="", validation_alias="CELERY_RESULT_BACKEND"
    )
    celery_task_eager: bool = Field(
        default=False, validation_alias="CELERY_TASK_ALWAYS_EAGER"
    )
    celery_worker_pool: str = Field(
        default="gevent",
        validation_alias="CELERY_WORKER_POOL",
        description="Worker 池：gevent（I/O 采集推荐）/ prefork / solo 等",
    )
    celery_worker_concurrency: int = Field(
        default=4,
        validation_alias="CELERY_WORKER_CONCURRENCY",
        description="并发 greenlet/子进程数，与 celery -c 一致",
    )
    celery_worker_prefetch_multiplier: int = Field(
        default=1,
        validation_alias="CELERY_WORKER_PREFETCH_MULTIPLIER",
        description="长任务建议 1，避免单 worker 囤积消息",
    )
    celery_beat_enabled: bool = Field(
        default=False, validation_alias="CELERY_BEAT_ENABLED"
    )
    async_schedule_beat_enabled: bool = Field(
        default=False, validation_alias="ASYNC_SCHEDULE_BEAT_ENABLED"
    )
    async_dispatch_poll_seconds: float = Field(
        default=15.0, validation_alias="ASYNC_DISPATCH_POLL_SECONDS"
    )
    async_dispatch_http_enabled: bool = Field(
        default=True, validation_alias="ASYNC_DISPATCH_HTTP_ENABLED"
    )
    async_restore_dispatch_due_on_startup: bool = Field(
        default=False, validation_alias="ASYNC_RESTORE_DISPATCH_DUE_ON_STARTUP"
    )
    async_dispatch_lock_ttl_seconds: int = Field(
        default=600, validation_alias="ASYNC_DISPATCH_LOCK_TTL_SECONDS"
    )
    async_task_redis_max_ttl_seconds: int = Field(
        default=604800, validation_alias="ASYNC_TASK_REDIS_MAX_TTL_SECONDS"
    )
    async_task_running_stale_seconds: float = Field(
        default=1800.0, validation_alias="ASYNC_TASK_RUNNING_STALE_SECONDS"
    )

    database_run_migrations: bool = Field(
        default=True, validation_alias="DATABASE_RUN_MIGRATIONS"
    )

    # 异步任务持久化（MySQL）；留空则仅同步 HTTP 可用，异步接口返回未配置
    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    database_auto_create_tables: bool = Field(
        default=False, validation_alias="ASYNC_TASK_DB_AUTO_CREATE"
    )
    async_results_default_limit: int = Field(
        default=20, validation_alias="ASYNC_RESULTS_DEFAULT_LIMIT"
    )

    # 异步任务提交前：yddm 用户校验（GET users/me）
    yddm_users_me_url: str = Field(
        default="https://api.yddm.com/users/me",
        validation_alias="YDDM_USERS_ME_URL",
    )
    yddm_users_me_timeout_sec: float = Field(
        default=10.0, validation_alias="YDDM_USERS_ME_TIMEOUT_SEC"
    )
    async_task_max_active_per_user: int = Field(
        default=10,
        validation_alias="ASYNC_TASK_MAX_ACTIVE_PER_USER",
    )

    # search-all 翻页止损（sync/async 共用 search_fetch_all；async_only=1 时仅 Celery 上下文生效）
    async_search_all_max_pages: int = Field(
        default=50, validation_alias="ASYNC_SEARCH_ALL_MAX_PAGES"
    )
    async_search_all_max_run_seconds: float = Field(
        default=900.0, validation_alias="ASYNC_SEARCH_ALL_MAX_RUN_SECONDS"
    )
    async_search_duplicate_page_threshold: int = Field(
        default=5, validation_alias="ASYNC_SEARCH_DUPLICATE_PAGE_THRESHOLD"
    )
    async_search_guards_async_only: bool = Field(
        default=True, validation_alias="ASYNC_SEARCH_GUARDS_ASYNC_ONLY"
    )

    def resolved_celery_broker(self) -> str:
        return (self.celery_broker_url or self.redis_url).strip()

    def resolved_celery_backend(self) -> str:
        return (self.celery_result_backend or self.redis_url).strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
