"""集中配置：从环境变量与 python 目录下 .env 读取。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# python/config/settings.py -> python/（含 .env）
_PY_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PY_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 第三方 API（与 workers 内 os.environ 兼容，进程加载 .env 后亦可不写代码）
    douyin_general_url: str = Field(default="", validation_alias="DOUYIN_GENERAL_URL")
    xhs_general_url: str = Field(default="", validation_alias="XHS_GENERAL_URL")

    # Celery / Redis
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", validation_alias="REDIS_URL")
    celery_broker_url: str = Field(default="", validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="", validation_alias="CELERY_RESULT_BACKEND")
    celery_task_eager: bool = Field(default=False, validation_alias="CELERY_TASK_ALWAYS_EAGER")
    celery_beat_enabled: bool = Field(default=False, validation_alias="CELERY_BEAT_ENABLED")

    def resolved_celery_broker(self) -> str:
        return (self.celery_broker_url or self.redis_url).strip()

    def resolved_celery_backend(self) -> str:
        return (self.celery_result_backend or self.redis_url).strip()

@lru_cache
def get_settings() -> Settings:
    return Settings()
