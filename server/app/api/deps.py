"""
FastAPI 依赖注入：数据库会话等。

路由中通过 `Depends(get_db)` 获取与请求绑定的 `Session`，请求结束自动关闭，避免连接泄漏。
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from app.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    为每个 HTTP 请求提供一个 SQLAlchemy `Session`。

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
