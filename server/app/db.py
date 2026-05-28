"""
数据库访问层：引擎与会话工厂。

职责：
- 从仓根 `.env` 加载 `DATABASE_URL`，创建 SQLAlchemy `Engine` 与 `sessionmaker`；
- 不承载业务 SQL，业务查询放在 `app.services` 或路由调用的服务函数中。

环境变量：
- `DATABASE_URL`：例如 `mysql+pymysql://user:pass@127.0.0.1:3306/feishu_keyword?charset=utf8mb4`
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.env_loader import load_server_dotenv

load_server_dotenv()

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
