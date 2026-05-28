"""MySQL / Redis 连通性探测（供 /ci-test）。"""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import text

from app.db import engine


def mysql_ok() -> bool:
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def redis_ok() -> bool:
    host = (os.getenv("REDIS_HOST") or "").strip()
    if not host:
        return False
    try:
        import redis

        port = int(os.getenv("REDIS_PORT", "6379"))
        password: Optional[str] = os.getenv("REDIS_PASSWORD") or None
        db = int(os.getenv("REDIS_DB", "0"))
        client = redis.Redis(
            host=host,
            port=port,
            password=password or None,
            db=db,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        client.ping()
        client.close()
        return True
    except Exception:
        return False
