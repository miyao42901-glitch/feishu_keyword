"""兼容入口：Celery 应用定义在 `social_platform.tasks.celery_app`。"""
from __future__ import annotations

from social_platform.tasks.celery_app import celery_app

__all__ = ["celery_app"]
