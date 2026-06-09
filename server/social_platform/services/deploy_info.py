"""部署版本与依赖探活（供 GET /api/v1/version）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import text

from config.settings import get_settings
from social_platform.debug_errors import expose_debug_details
from social_platform.redis_client import ping_redis, redis_configured

_SERVER_ROOT = Path(__file__).resolve().parent.parent.parent
_BUILD_INFO_PATH = _SERVER_ROOT / "BUILD_INFO"


def load_build_info() -> dict[str, str]:
    if not _BUILD_INFO_PATH.is_file():
        return {}
    info: dict[str, str] = {}
    for line in _BUILD_INFO_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, val = line.partition("=")
        info[key.strip()] = val.strip()
    return info


def check_mysql_status() -> dict[str, Any]:
    url = get_settings().database_url.strip()
    if not url:
        return {"status": "unconfigured", "configured": False}
    try:
        from social_platform.database.session import get_engine

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "configured": True}
    except Exception as exc:
        err_limit = 2000 if expose_debug_details() else 200
        out: dict[str, Any] = {
            "status": "error",
            "configured": True,
            "error": str(exc)[:err_limit],
        }
        if expose_debug_details():
            out["error_type"] = type(exc).__name__
        return out


def check_redis_status() -> dict[str, Any]:
    if not redis_configured():
        return {"status": "unconfigured", "configured": False}
    if ping_redis():
        return {"status": "ok", "configured": True}
    out: dict[str, Any] = {"status": "error", "configured": True}
    if expose_debug_details():
        out["error"] = "redis ping failed"
        out["redis_url"] = get_settings().redis_url.split("@")[-1]
    return out


def build_version_payload() -> dict[str, Any]:
    build_info = load_build_info()
    mysql = check_mysql_status()
    redis_st = check_redis_status()

    service_status = "ok"
    if mysql["status"] == "error" or redis_st["status"] == "error":
        service_status = "degraded"

    deploy = {
        "build": build_info.get("build", ""),
        "commit": build_info.get("commit", ""),
        "branch": build_info.get("branch", ""),
        "deployed_at": build_info.get("deployed_at", ""),
        "environment": build_info.get("environment")
        or get_settings().environment
        or "",
        "pipeline": build_info.get("pipeline", ""),
    }

    payload: dict[str, Any] = {
        "service": {"status": service_status},
        "mysql": mysql,
        "redis": redis_st,
        "deploy": deploy,
    }
    if expose_debug_details():
        s = get_settings()
        payload["debug"] = {
            "database_configured": bool(s.database_url.strip()),
            "celery_broker_configured": bool(s.celery_broker_url.strip()),
            "celery_backend_configured": bool(s.celery_result_backend.strip()),
        }
    return payload
