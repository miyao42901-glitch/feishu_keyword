"""管理端 FastAPI 依赖。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, Optional

from fastapi import Header
from sqlalchemy.orm import Session

from admin.exceptions import AdminHttpError
from admin.session import resolve_admin_token
from social_platform.database.session import get_session_factory


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


@dataclass(frozen=True)
class AdminContext:
    admin_id: int
    profile: dict[str, Any]


def require_admin(token: Optional[str] = Header(default=None)) -> AdminContext:
    payload = resolve_admin_token(token or "")
    if not payload:
        raise AdminHttpError(40101, "未登录或 token 失效", http_status=401)
    admin_id = int(payload.get("admin_id") or 0)
    if admin_id <= 0:
        raise AdminHttpError(40101, "未登录或 token 失效", http_status=401)
    profile = payload.get("profile")
    if not isinstance(profile, dict):
        profile = {}
    return AdminContext(admin_id=admin_id, profile=profile)
