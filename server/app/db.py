"""
数据库访问层：引擎、会话工厂、连通性探测。

职责：
- 从 `server/.env` 加载 `DATABASE_URL`，创建 SQLAlchemy `Engine` 与 `sessionmaker`；
- 不承载业务 SQL，业务查询放在 `app.services` 或路由调用的服务函数中。

环境变量：
- `DATABASE_URL`：例如 `mysql+pymysql://user:pass@127.0.0.1:3306/feishu_keyword?charset=utf8mb4`
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 无论从哪个工作目录启动，都加载 server/.env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

engine = None
SessionLocal: Optional[sessionmaker] = None

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_database() -> Tuple[bool, Optional[str]]:
    """
    探测当前配置的 MySQL 是否可连接。

    Returns:
        (True, None) 表示连接成功；
        (False, 'not_configured') 表示未设置 `DATABASE_URL`；
        (False, 错误信息字符串) 表示连接失败（密码错误、服务未启动等）。
    """
    if engine is None:
        return False, "not_configured"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:  # noqa: BLE001 — 健康检查需要把原因返回给调用方
        return False, str(exc)
