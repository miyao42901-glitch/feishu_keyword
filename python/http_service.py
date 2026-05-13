"""单进程 HTTP：对外 API 由 `http_api` 按版本挂载。"""
from __future__ import annotations

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

from fastapi import FastAPI  # noqa: E402

from http_api.v1.routes import register_v1_routes  # noqa: E402

app = FastAPI(title="social_http", version="1.0.0")

register_v1_routes(app)
