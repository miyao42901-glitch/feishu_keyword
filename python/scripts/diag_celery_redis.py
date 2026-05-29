"""诊断 Redis / Celery broker（python scripts/diag_celery_redis.py）。"""
from __future__ import annotations

import sys
from pathlib import Path

_PY = Path(__file__).resolve().parent.parent
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

from social_platform.env_bootstrap import ensure_dotenv_loaded

ensure_dotenv_loaded()

import logging

from config.settings import get_settings
from social_platform.celery_broker import ensure_celery_startup_health, safe_apply_async
from social_platform.celery_env import log_celery_broker_env

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("diag")

s = get_settings()
print("=== settings ===")
print("REDIS_URL:", s.redis_url)
print("CELERY_BROKER:", s.resolved_celery_broker())
print("CELERY_BACKEND:", s.resolved_celery_backend())
print("CELERY_EAGER:", s.celery_task_eager)

log_celery_broker_env(log)
ensure_celery_startup_health(log)

if s.celery_require_worker_online:
    from social_platform.celery_broker import celery_workers_online

    if not celery_workers_online():
        print(
            "SKIP safe_apply_async: Celery worker offline "
            "(先启动: celery -A social_platform.tasks.celery_app worker -l info -P solo)"
        )
    else:
        from social_platform.tasks.worker_tasks import run_social_async_task

        ar = safe_apply_async(
            run_social_async_task,
            task_id=999999,
            apply_kwargs={"args": [999999, "diag-test-key"], "countdown": 3600},
        )
        print("safe_apply_async OK id=", ar.id)
else:
    print("CELERY_REQUIRE_WORKER_ONLINE=0, skip apply_async dispatch test")
