"""启动时应用轻量 SQL 迁移（feishu_async_tasks 列对齐、管理端 RBAC）。"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def _column_names(engine: Engine, table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SHOW COLUMNS FROM {table}")).fetchall()
    return {str(r[0]) for r in rows}


def _index_names(engine: Engine, table: str) -> set[str]:
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
    if not _table_exists(engine, "feishu_async_tasks"):
        return
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
        logger.info("skip feishu_async_tasks migrations: table missing")
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


def apply_analytics_migrations(engine: Engine) -> None:
    """埋点事实表（幂等）。"""
    if _table_exists(engine, "analytics_user"):
        return
    path = _MIGRATIONS_DIR / "014_analytics_tracking.sql"
    _execute_sql_file(engine, path)
    logger.info("analytics tracking schema applied")


def apply_pending_migrations(engine: Engine) -> None:
    try:
        apply_admin_backoffice_migrations(engine)
        apply_analytics_migrations(engine)
        apply_feishu_async_tasks_migrations(engine)
        apply_p0_index_optimizations(engine)
    except Exception:
        logger.exception("database migration failed")
        raise


def _table_exists(engine: Engine, table: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = :t
                """
            ),
            {"t": table},
        ).scalar()
        return int(row or 0) > 0


def _split_sql_statements(raw: str) -> list[str]:
    lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        lines.append(line)
    body = "\n".join(lines)
    parts = re.split(r";\s*\n", body)
    return [p.strip() for p in parts if p.strip()]


def _execute_sql_file(engine: Engine, path: Path) -> None:
    if not path.is_file():
        logger.warning("migration file missing: %s", path)
        return
    statements = _split_sql_statements(path.read_text(encoding="utf-8"))
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    logger.info("executed migration file %s", path.name)


def apply_admin_backoffice_migrations(engine: Engine) -> None:
    """创建 sys_* 管理端表并写入开发种子（幂等）。"""
    if _table_exists(engine, "sys_admin"):
        return
    schema_sql = _MIGRATIONS_DIR / "012_create_sys_backoffice_rbac.sql"
    seed_sql = _MIGRATIONS_DIR / "013_seed_sys_backoffice_dev.sql"
    _execute_sql_file(engine, schema_sql)
    if _table_exists(engine, "sys_admin"):
        _execute_sql_file(engine, seed_sql)
        logger.info("admin backoffice schema + seed applied")
