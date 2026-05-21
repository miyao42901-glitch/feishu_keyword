"""管理端：登录 / 登出。"""

from __future__ import annotations

from datetime import datetime

import bcrypt
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.admin_session import issue_admin_token, revoke_admin_token
from app.api.deps import get_db
from app.schemas.admin_response import admin_fail, admin_ok
from fastapi import Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/system", tags=["管理端-系统"])


class AdminLoginBody(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


def _verify_password(plain: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


@router.post("/login")
def admin_login(body: AdminLoginBody, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT id, username, password_hash, nickname, is_disable, is_delete
            FROM sys_admin WHERE username = :u LIMIT 1
            """
        ),
        {"u": body.username.strip()},
    ).mappings().first()

    if not row or row.get("is_delete"):
        return admin_fail(10001, "账号或密码错误")
    if row.get("is_disable"):
        return admin_fail(10002, "账号已禁用")

    if not _verify_password(body.password, row.get("password_hash")):
        return admin_fail(10001, "账号或密码错误")

    admin_id = int(row["id"])
    profile = {
        "id": admin_id,
        "username": row.get("username"),
        "nickname": row.get("nickname") or "",
        "is_super": admin_id == 1,
    }
    token = issue_admin_token(admin_id, profile)
    db.execute(
        text("UPDATE sys_admin SET last_login_at = :t WHERE id = :id"),
        {"t": datetime.now(), "id": admin_id},
    )
    db.commit()

    return admin_ok(
        data={
            "token": token,
            "admin": profile,
        }
    )


@router.post("/logout")
def admin_logout(request: Request, token: str | None = Header(default=None)):
    tok = token or request.headers.get("token")
    if tok:
        revoke_admin_token(tok)
    return admin_ok()
