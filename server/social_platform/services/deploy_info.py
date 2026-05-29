"""部署版本与依赖探活（供 GET /api/v1/version）。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy import text

from config.settings import get_settings
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
        return {
            "status": "error",
            "configured": True,
            "error": str(exc)[:200],
        }


def check_redis_status() -> dict[str, Any]:
    if not redis_configured():
        return {"status": "unconfigured", "configured": False}
    if ping_redis():
        return {"status": "ok", "configured": True}
    return {"status": "error", "configured": True}


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
        or os.getenv("ENVIRONMENT", ""),
        "pipeline": build_info.get("pipeline", ""),
    }

    return {
        "service": {"status": service_status},
        "mysql": mysql,
        "redis": redis_st,
        "deploy": deploy,
    }
