"""与 social_platform.aggregated_job.run_task 复用：同步执行抓取逻辑，供异步队列或 Beat 调用。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PY = Path(__file__).resolve().parent.parent.parent
_workers = _PY / "workers"
for p in (_workers, _PY):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from social_platform.env_bootstrap import ensure_dotenv_loaded

ensure_dotenv_loaded()

from celery_jobs.celery_app import celery_app  # noqa: E402

TASK_JZL_SOCIAL = "celery_jobs.tasks.social_task.run_jzl_social"


@celery_app.task(name=TASK_JZL_SOCIAL)
def run_jzl_social(payload: dict[str, Any]) -> dict[str, Any]:
    from social_platform.aggregated_job import run_task

    return run_task(payload)
