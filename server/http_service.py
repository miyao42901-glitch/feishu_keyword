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

from config.settings import get_settings as _load_settings  # noqa: E402
from social_platform.utils.app_logging import AppLogConfig  # noqa: E402

_log_settings = _load_settings()
AppLogConfig.setup(
    "http",
    log_dir=_log_settings.log_dir or None,
    level=_log_settings.log_level,
    retention_days=_log_settings.log_retention_days,
)

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from admin.exceptions import register_admin_exception_handlers  # noqa: E402
from admin.router import register_admin_routes  # noqa: E402
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

# 管理台静态域与 API 域分离时需 CORS（如 test-fskw-admin → test-fskw）
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://[^\s]+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_api_exception_handlers(app)
register_admin_exception_handlers(app)
register_v1_routes(app)
register_admin_routes(app)
