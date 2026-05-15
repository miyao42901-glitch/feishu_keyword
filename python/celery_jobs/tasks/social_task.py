"""兼容：任务已迁至 `social_platform.tasks.worker_tasks`。"""
from __future__ import annotations

from social_platform.tasks.worker_tasks import TASK_JZL_SOCIAL, run_jzl_social  # noqa: F401

__all__ = ["TASK_JZL_SOCIAL", "run_jzl_social"]
