"""单进程 HTTP：对外 API 由 `http_api` 按版本挂载。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_PY = Path(__file__).resolve().parent
_workers = _PY / "workers"
for p in (_workers, _PY):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from social_platform.env_bootstrap import ensure_dotenv_loaded  # noqa: E402

ensure_dotenv_loaded()

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402

from config.settings import get_settings  # noqa: E402
from http_api.v1.routes import register_v1_routes  # noqa: E402
from social_platform.api_response import register_api_exception_handlers  # noqa: E402

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    s = get_settings()
    if s.async_dispatch_http_enabled and s.async_schedule_beat_enabled:
        logger.warning(
            "dual_dispatch_warning",
            extra={
                "dispatch_mode": "http+beat",
                "duplicate_dispatch_risk": True,
                "dual_dispatch_warning": 1,
            },
        )
    if s.database_url.strip():
        from social_platform.database.session import get_engine, init_db_tables

        if s.database_auto_create_tables:
            init_db_tables()
        if s.database_run_migrations:
            from social_platform.database.db_migrate import apply_pending_migrations

            apply_pending_migrations(get_engine())
        if s.async_dispatch_http_enabled or s.async_schedule_beat_enabled:
            from social_platform.celery_broker import ensure_celery_startup_health

            ensure_celery_startup_health(logger)
    from social_platform.services.async_dispatch_loop import start_async_dispatch_loop

    start_async_dispatch_loop()
    yield


app = FastAPI(title="social_http", version="1.0.0", lifespan=_lifespan)

register_api_exception_handlers(app)
register_v1_routes(app)
