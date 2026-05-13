"""各 Worker FastAPI 入口复用。"""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from social_platform.env_bootstrap import ensure_dotenv_loaded

ensure_dotenv_loaded()

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from social_platform.api_response import from_worker_run, ok
from social_platform.schemas import TaskEnvelope

from http_api.versions import API_V1_PREFIX


def create_worker_app(name: str, run_task: Callable[[dict[str, Any]], dict[str, Any]]) -> FastAPI:
    app = FastAPI(title=name, version="1.0.0")
    r = APIRouter()

    @r.get("/health")
    def health() -> dict[str, Any]:
        return ok(data={"service": name, "status": "ok"})

    @r.post("/run")
    def run(body: TaskEnvelope) -> JSONResponse:
        raw = run_task(body.model_dump())
        return JSONResponse(from_worker_run(raw))

    app.include_router(r, prefix=API_V1_PREFIX)
    return app


def run_uvicorn(app: FastAPI, *, default_port: int, default_host: str = "0.0.0.0") -> None:
    import uvicorn

    host = os.environ.get("WORKER_HOST", default_host).strip() or default_host
    port = int(os.environ.get("WORKER_PORT", str(default_port)))
    uvicorn.run(app, host=host, port=port)
