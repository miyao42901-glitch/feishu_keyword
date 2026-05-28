"""启动时应用基线建表与轻量 SQL 迁移（feishu_async_tasks 列对齐、P0 索引）。"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _PY_ROOT / "migrations"
_SCHEMA_SQL = _MIGRATIONS_DIR / "schema.sql"
_BASELINE_TABLE = "feishu_async_tasks"


def _table_exists(engine: Engine, table: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = :t LIMIT 1"
            ),
            {"t": table},
        ).first()
    return row is not None


def _iter_create_statements(sql_text: str) -> list[str]:
    """从 schema.sql 提取 CREATE TABLE 语句（忽略注释与尾部 ALTER 说明）。"""
    lines: list[str] = []
    for line in sql_text.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    body = "\n".join(lines)
    out: list[str] = []
    for chunk in body.split(";"):
        stmt = chunk.strip()
        if re.match(r"^CREATE\s+TABLE\b", stmt, flags=re.IGNORECASE):
            out.append(stmt)
    return out


def apply_baseline_schema_if_needed(engine: Engine) -> None:
    """新库/空库：执行 schema.sql 全量 CREATE TABLE（幂等）。"""
    if _table_exists(engine, _BASELINE_TABLE):
        return
    if not _SCHEMA_SQL.is_file():
        raise FileNotFoundError(f"baseline schema missing: {_SCHEMA_SQL}")
    logger.info("baseline: %s 不存在，应用 %s", _BASELINE_TABLE, _SCHEMA_SQL.name)
    statements = _iter_create_statements(_SCHEMA_SQL.read_text(encoding="utf-8"))
    if not statements:
        raise RuntimeError(f"no CREATE TABLE statements in {_SCHEMA_SQL}")
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    logger.info("baseline: applied %d CREATE TABLE statement(s)", len(statements))


def _column_names(engine: Engine, table: str) -> set[str]:
    if not _table_exists(engine, table):
        return set()
    with engine.connect() as conn:
        rows = conn.execute(text(f"SHOW COLUMNS FROM `{table}`")).fetchall()
    return {str(r[0]) for r in rows}


def _index_names(engine: Engine, table: str) -> set[str]:
    if not _table_exists(engine, table):
        return set()
    with engine.connect() as conn:
        rows = conn.execute(text(f"SHOW INDEX FROM `{table}`")).fetchall()
    return {str(r[2]) for r in rows}


# (table, index_name, ddl_suffix) — P0 组合索引
_P0_INDEXES: tuple[tuple[str, str, str], ...] = (
    (
        "feishu_async_tasks",
        "ix_async_tasks_user_status_id",
        "(user_id, status, id DESC)",
    ),
    (
        "feishu_douyin_results",
        "ix_feishu_douyin_results_task_upload_ct",
        "(task_id, is_upload, create_time DESC)",
    ),
    (
        "feishu_douyin_results",
        "ix_feishu_douyin_results_user_upload_id",
        "(user_id, is_upload, id)",
    ),
    (
        "feishu_xhs_results",
        "ix_feishu_xhs_results_task_upload_ct",
        "(task_id, is_upload, create_time DESC)",
    ),
    (
        "feishu_xhs_results",
        "ix_feishu_xhs_results_user_upload_id",
        "(user_id, is_upload, id)",
    ),
    (
        "feishu_wxvideo_results",
        "ix_feishu_wxvideo_results_task_upload_ct",
        "(task_id, is_upload, create_time DESC)",
    ),
    (
        "feishu_wxvideo_results",
        "ix_feishu_wxvideo_results_user_upload_id",
        "(user_id, is_upload, id)",
    ),
    (
        "feishu_mp_results",
        "ix_feishu_mp_results_task_upload_ct",
        "(task_id, is_upload, create_time DESC)",
    ),
    (
        "feishu_mp_results",
        "ix_feishu_mp_results_user_upload_id",
        "(user_id, is_upload, id)",
    ),
)


def apply_p0_index_optimizations(engine: Engine) -> None:
    """P0 索引：任务列表、结果分页、待验收（幂等）。"""
    tables = {t for t, _, _ in _P0_INDEXES}
    existing_by_table = {t: _index_names(engine, t) for t in tables}
    with engine.begin() as conn:
        for table, index_name, columns in _P0_INDEXES:
            if index_name in existing_by_table.get(table, set()):
                continue
            conn.execute(
                text(f"ALTER TABLE `{table}` ADD INDEX `{index_name}` {columns}")
            )
            existing_by_table.setdefault(table, set()).add(index_name)
            logger.info("added %s on %s", index_name, table)


def apply_feishu_async_tasks_migrations(engine: Engine) -> None:
    """对齐 feishu_async_tasks 关键列（interval/fetch_count/api_key）。"""
    if not _table_exists(engine, "feishu_async_tasks"):
        logger.warning("skip feishu_async_tasks column migrations: table missing")
        return
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

        if "task_name" not in cols:
            conn.execute(
                text(
                    """
                    ALTER TABLE feishu_async_tasks
                    ADD COLUMN task_name VARCHAR(100) NOT NULL DEFAULT ''
                        COMMENT '任务名称（1～100 字符）'
                        AFTER user_id
                    """
                )
            )
            logger.info("added feishu_async_tasks.task_name")
            cols.add("task_name")


def apply_pending_migrations(engine: Engine) -> None:
    try:
        apply_baseline_schema_if_needed(engine)
        apply_feishu_async_tasks_migrations(engine)
        apply_p0_index_optimizations(engine)
    except Exception:
        logger.exception("database migration failed")
        raise
