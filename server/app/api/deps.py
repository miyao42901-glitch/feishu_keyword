"""
FastAPI 依赖注入：数据库会话等。

路由中通过 `Depends(get_db)` 获取与请求绑定的 `Session`，请求结束自动关闭，避免连接泄漏。
"""

from __future__ import annotations

from typing import Generator

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    为每个 HTTP 请求提供一个 SQLAlchemy `Session`（路由中 `Depends(get_db)`）。

    请求结束自动 `close()`，避免连接泄漏；业务层在同一 `Session` 内提交事务。

    Yields:
        绑定到全局引擎的数据库会话。

    Raises:
        RuntimeError: 未配置 `DATABASE_URL` 或引擎初始化失败时。
    """
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not set or invalid")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_feishu_api_key(
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
) -> str:
    """
    飞书插件任务接口：按请求头 `X-Api-Key` 识别账户（与前端持久化的 YDDM API Key 一致）。

    Returns:
        去首尾空白后的 API Key。

    Raises:
        HTTPException: 401 — 未携带或 Key 为空。
    """
    key = (x_api_key or "").strip()
    if not key:
        raise HTTPException(
            status_code=401,
            detail="请先登录并在顶部获取 API Key 后再访问任务数据",
        )
    return key
