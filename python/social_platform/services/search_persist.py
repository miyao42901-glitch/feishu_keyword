"""
采集落库：search-all 支持按页写入；整任务结束后可选再调一次（已按页落库则跳过）。

不抛出到业务层：失败只打日志。
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from config.settings import get_settings
from social_platform.actions.registry import platform_for_persist
from social_platform.services.result_store_service import save_search_results

logger = logging.getLogger(__name__)


@dataclass
class SearchAllAsyncPersistState:
    """Celery 执行 search-all 时由 task_executor 注入，Worker 每页回调读取。"""

    db: Session
    task_id: int
    run_id: str
    user_id: str
    public_action: str
    body: dict[str, Any]


search_all_async_ctx: ContextVar[Optional[SearchAllAsyncPersistState]] = ContextVar(
    "search_all_async_ctx", default=None
)


def bind_search_all_async_persist(state: SearchAllAsyncPersistState) -> Any:
    return search_all_async_ctx.set(state)


def unbind_search_all_async_persist(token: Any) -> None:
    search_all_async_ctx.reset(token)


def platform_from_action(action: str) -> Optional[str]:
    """兼容旧 `douyin_*` / 新 kebab-case：返回用于落库结果表的平台标识。"""
    return platform_for_persist(action)


def extract_result_rows(data: Any) -> list[Any]:
    """从 worker 返回的 data 中取出列表行（search-page 与 search-all 兼容）。"""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        rec = data.get("records")
        if isinstance(rec, list):
            return rec
        inner = data.get("data")
        if isinstance(inner, list):
            return inner
    return []


def try_save_search_result_chunk(
    action: str,
    body: dict[str, Any],
    rows: list[Any],
    *,
    user_id: str,
    task_id: int | str | None = None,
    run_id: str = "",
) -> Optional[dict[str, Any]]:
    """search-all 单页结果落库；异常吞掉。``rows`` 为空时返回 None。"""
    try:
        platform = platform_from_action(str(action or ""))
        if not platform:
            return None
        if not get_settings().database_url.strip():
            return None
        uid = (user_id or "").strip()
        if not uid:
            return None
        keyword = str((body or {}).get("keyword") or "")
        if not rows:
            return None
        stats = save_search_results(
            platform, keyword, rows, user_id=uid, task_id=task_id
        )
        logger.info(
            "search results chunk persisted action=%s platform=%s task_id=%s run_id=%s user_id=%s stats=%s",
            action,
            platform,
            task_id,
            run_id,
            uid,
            stats,
        )
        return stats
    except Exception:
        logger.exception(
            "search results chunk persist failed action=%s task_id=%s run_id=%s",
            action,
            task_id,
            run_id,
        )
        return None


def try_save_search_after_crawl(
    action: str,
    body: dict[str, Any],
    raw: dict[str, Any],
    *,
    user_id: str,
    task_id: int | str | None = None,
) -> Optional[dict[str, Any]]:
    """
    在返回 HTTP 前 / 异步任务写结果前调用；任何异常吞掉并打日志。

    :param body: 与落库/搜索相关的参数字典（异步任务为 `body_json`；同步仍为 worker params）
    :return: save_search_results 的统计；未执行落库时返回 None。
    """
    try:
        if not raw.get("ok"):
            return None
        data = raw.get("data")
        if isinstance(data, dict) and data.get("_incremental_persist"):
            logger.debug(
                "skip bulk search persist: already persisted per page action=%s", action
            )
            return None
        platform = platform_from_action(str(action or ""))
        if not platform:
            return None
        if not get_settings().database_url.strip():
            logger.debug("skip search persist: DATABASE_URL empty action=%s", action)
            return None
        uid = (user_id or "").strip()
        if not uid:
            logger.debug("skip search persist: empty user_id action=%s", action)
            return None
        keyword = str((body or {}).get("keyword") or "")
        rows = extract_result_rows(raw.get("data"))
        if not rows:
            return None
        stats = save_search_results(
            platform, keyword, rows, user_id=uid, task_id=task_id
        )
        logger.info(
            "search results persisted action=%s platform=%s task_id=%s user_id=%s stats=%s",
            action,
            platform,
            task_id,
            uid,
            stats,
        )
        return stats
    except Exception:
        logger.exception(
            "search results persist failed action=%s task_id=%s", action, task_id
        )
        return None


def _stat_int(stats: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key in stats:
            try:
                return int(stats.get(key) or 0)
            except (TypeError, ValueError):
                return 0
    return 0


def persist_stats_for_task_row(stats: dict[str, Any]) -> tuple[int, int, int, int, int]:
    """将 save 统计映射为异步任务表上的 success_count / failed_count 增量。"""
    inserted = _stat_int(stats, "inserted_count", "inserted")
    duplicated = _stat_int(stats, "duplicated_count", "duplicated")
    skipped = _stat_int(stats, "skipped_count", "skipped")
    persist_errors = _stat_int(stats, "failed_count", "persist_errors")
    # success_count 仅统计真实成功入库数量，避免 duplicated 拉高抓取进度。
    success_delta = inserted
    failed_delta = duplicated + skipped + persist_errors
    return success_delta, failed_delta, inserted, duplicated, persist_errors


def apply_search_persist_stats_to_async_task(
    db: Session,
    task_id: int,
    stats: dict[str, Any],
) -> None:
    """在 Celery 任务同一 Session 内累加 success_count / failed_count（不写采集明细表）。"""
    from social_platform.models.async_task import AsyncTask

    task = db.get(AsyncTask, task_id)
    if task is None:
        return
    (
        s_delta,
        f_delta,
        inserted_count,
        duplicated_count,
        failed_count,
    ) = persist_stats_for_task_row(stats)
    task.success_count = int(task.success_count or 0) + s_delta
    task.failed_count = int(task.failed_count or 0) + f_delta

    platform = platform_from_action(str(task.action or "")) or "unknown"
    if duplicated_count > 0:
        logger.info(
            "duplicate skipped",
            extra={
                "task_id": int(task_id),
                "run_id": str(getattr(task, "current_run_id", "") or ""),
                "platform": platform,
                "duplicated_count": int(duplicated_count),
            },
        )
    logger.info(
        "persist_result",
        extra={
            "task_id": int(task_id),
            "run_id": str(getattr(task, "current_run_id", "") or ""),
            "platform": platform,
            "inserted_count": int(inserted_count),
            "duplicated_count": int(duplicated_count),
            "failed_count": int(failed_count),
            "success_count": int(task.success_count or 0),
            "fetch_count": int(getattr(task, "fetch_count", 0) or 0),
        },
    )
    db.add(task)


def persist_search_all_page_if_async(chunk: list[Any]) -> int:
    """Celery 上下文中对当前页落库并累加任务计数；返回本页真实 inserted_count。"""
    ctx = search_all_async_ctx.get()
    if ctx is None or not chunk:
        if ctx is None:
            logger.debug("skip async page persist: missing async context")
        elif not chunk:
            logger.debug("skip async page persist: empty chunk")
        return 0
    stats = try_save_search_result_chunk(
        ctx.public_action,
        ctx.body,
        chunk,
        user_id=ctx.user_id,
        task_id=int(ctx.task_id),
        run_id=ctx.run_id,
    )
    if stats:
        logger.info(
            "search-all chunk saved task_id=%s run_id=%s inserted=%s duplicated=%s skipped=%s persist_errors=%s",
            int(ctx.task_id),
            str(ctx.run_id or ""),
            int(_stat_int(stats, "inserted_count", "inserted")),
            int(_stat_int(stats, "duplicated_count", "duplicated")),
            int(_stat_int(stats, "skipped_count", "skipped")),
            int(_stat_int(stats, "failed_count", "persist_errors")),
        )
        apply_search_persist_stats_to_async_task(ctx.db, int(ctx.task_id), stats)
        ctx.db.commit()
        return int(_stat_int(stats, "inserted_count", "inserted"))
    logger.warning(
        "search-all chunk persist skipped/failed task_id=%s run_id=%s action=%s",
        int(ctx.task_id),
        str(ctx.run_id or ""),
        ctx.public_action,
    )
    return 0
