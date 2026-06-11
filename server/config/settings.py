"""集中配置：从环境变量与 python 目录下 .env 读取。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

<<<<<<< HEAD
# python/config/settings.py -> python/（含 .env）
_PY_ROOT = Path(__file__).resolve().parent.parent
=======
# server/config/settings.py -> 仓根（.env / .env.local）+ server/.env 兜底
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SERVER_ROOT = Path(__file__).resolve().parent.parent
>>>>>>> lyc


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
<<<<<<< HEAD
        env_file=str(_PY_ROOT / ".env"),
=======
        env_file=(
            str(_REPO_ROOT / ".env"),
            str(_REPO_ROOT / ".env.local"),
            str(_SERVER_ROOT / ".env"),
        ),
>>>>>>> lyc
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
    celery_require_worker_online: bool = Field(
        default=True,
        validation_alias="CELERY_REQUIRE_WORKER_ONLINE",
        description="派发前 control.ping；无 worker 时阻止 apply_async",
    )
    celery_apply_async_max_retries: int = Field(
        default=3, validation_alias="CELERY_APPLY_ASYNC_MAX_RETRIES"
    )
    celery_apply_async_backoff_base: float = Field(
        default=1.0, validation_alias="CELERY_APPLY_ASYNC_BACKOFF_BASE"
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
        default=120.0, validation_alias="ASYNC_TASK_RUNNING_STALE_SECONDS"
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

    log_dir: str = Field(
        default="",
        validation_alias="LOG_DIR",
        description="日志目录，空则使用 python/logs",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_retention_days: int = Field(
        default=7,
        validation_alias="LOG_RETENTION_DAYS",
        description="日志文件保留天数（按天滚动 + 启动时清理过期文件）",
    )

    def resolved_celery_broker(self) -> str:
        from social_platform.celery_broker import require_redis_celery_url

        return require_redis_celery_url(self.celery_broker_url, "CELERY_BROKER_URL")

    def resolved_celery_backend(self) -> str:
        from social_platform.celery_broker import require_redis_celery_url

        return require_redis_celery_url(
            self.celery_result_backend, "CELERY_RESULT_BACKEND"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
