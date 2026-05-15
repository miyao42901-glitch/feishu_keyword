"""Beat 调度表：实现位于 `social_platform.tasks.beat_schedule`。"""
from __future__ import annotations

from social_platform.tasks.beat_schedule import build_beat_schedule
from social_platform.tasks.worker_tasks import TASK_JZL_SOCIAL

__all__ = ["build_beat_schedule", "TASK_JZL_SOCIAL"]
