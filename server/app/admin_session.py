"""管理端 token：Redis 存储，Header `token` 传递。"""

from __future__ import annotations

import json
import os
import secrets
import uuid
from typing import Any, Optional

ADMIN_TOKEN_PREFIX = "fkw:admin:token:"
ADMIN_TOKEN_TTL_SEC = 86400 * 7


def _redis_client():
    import redis

    host = (os.getenv("REDIS_HOST") or "").strip()
    if not host:
        return None
    return redis.Redis(
        host=host,
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD") or None,
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
        socket_connect_timeout=3,
    )


def issue_admin_token(admin_id: int, profile: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    client = _redis_client()
    if client is None:
        return f"local-{admin_id}-{uuid.uuid4().hex}"
    payload = {"admin_id": admin_id, "profile": profile}
    client.setex(f"{ADMIN_TOKEN_PREFIX}{token}", ADMIN_TOKEN_TTL_SEC, json.dumps(payload))
    return token


def revoke_admin_token(token: str) -> None:
    if not token or token.startswith("local-"):
        return
    client = _redis_client()
    if client:
        client.delete(f"{ADMIN_TOKEN_PREFIX}{token}")


def resolve_admin_token(token: str) -> Optional[dict[str, Any]]:
    if not token:
        return None
    if token.startswith("local-"):
        parts = token.split("-")
        if len(parts) >= 2 and parts[1].isdigit():
            return {"admin_id": int(parts[1]), "profile": {}}
        return None
    client = _redis_client()
    if not client:
        return None
    raw = client.get(f"{ADMIN_TOKEN_PREFIX}{token}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
