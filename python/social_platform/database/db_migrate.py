"""启动时应用轻量 SQL 迁移（feishu_async_tasks 列对齐）。"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _column_names(engine: Engine, table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SHOW COLUMNS FROM {table}")).fetchall()
    return {str(r[0]) for r in rows}


def apply_feishu_async_tasks_migrations(engine: Engine) -> None:
    """对齐 feishu_async_tasks 关键列（interval/fetch_count/api_key）。"""
    cols = _column_names(engine, "feishu_async_tasks")

    with engine.begin() as conn:
        if "collect_interval_minutes" in cols and "interval_minutes" not in cols:
            conn.execute(
                text(
                    """
                    ALTER TABLE feishu_async_tasks
                    CHANGE COLUMN collect_interval_minutes interval_minutes INT NOT NULL DEFAULT 60
                        COMMENT '定时采集频率（分钟），最小 5，默认 60'
                    """
                )
            )
            logger.info("migrated collect_interval_minutes -> interval_minutes")
            cols.discard("collect_interval_minutes")
            cols.add("interval_minutes")

        if "fetch_count" not in cols:
            conn.execute(
                text(
                    """
                    ALTER TABLE feishu_async_tasks
                    ADD COLUMN fetch_count INT NOT NULL DEFAULT 100
                        COMMENT '单次采集条数上限，1～500，默认 100'
                        AFTER interval_minutes
                    """
                )
            )
            logger.info("added feishu_async_tasks.fetch_count")
            cols.add("fetch_count")

        if "api_key" not in cols:
            conn.execute(
                text(
                    """
                    ALTER TABLE feishu_async_tasks
                    ADD COLUMN api_key VARCHAR(128) NOT NULL DEFAULT ''
                        COMMENT '提交任务的API_KEY'
                        AFTER body_json
                    """
                )
            )
            logger.info("added feishu_async_tasks.api_key")
            cols.add("api_key")


def apply_pending_migrations(engine: Engine) -> None:
    try:
        apply_feishu_async_tasks_migrations(engine)
    except Exception:
        logger.exception("database migration failed")
        raise
