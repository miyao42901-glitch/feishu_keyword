from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker[Session]] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = get_settings().database_url.strip()
        if not url:
            raise RuntimeError("DATABASE_URL is empty")
        _engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def init_db_tables() -> None:
    """建表（仅开发/首次部署；生产建议用迁移工具）。"""
    from social_platform.models import async_task as _at  # noqa: F401
    from social_platform.models.base import Base
    from social_platform.models.results import douyin_search_result as _dr  # noqa: F401
    from social_platform.models.results import xhs_search_result as _xr  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
