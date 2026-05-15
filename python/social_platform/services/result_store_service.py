"""
统一采集结果持久化：按 platform 路由到 `feishu_*_results` 表；同步 HTTP 与 Celery 共用。

- 插入侧不显式写 `is_upload`，由数据库默认 0。
- 不落库原始 JSON；仅写入定长业务列。
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Iterable, Optional, Type

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config.settings import get_settings
from social_platform.database.session import session_scope
from social_platform.models.base import Base
from social_platform.models.results.registry import get_result_model

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500
_MODAL_ID_RE = re.compile(r"modal_id=(\d+)", re.IGNORECASE)


def _coerce_task_id_optional(task_id: Any) -> Optional[int]:
    if task_id is None:
        return None
    if isinstance(task_id, bool):
        return None
    if isinstance(task_id, int):
        return task_id if task_id > 0 else None
    s = str(task_id).strip()
    if s.isdigit():
        n = int(s)
        return n if n > 0 else None
    return None


def _truncate(s: str, max_len: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[:max_len]


def _first_url(seq: Any, max_len: int = 256) -> str:
    if not isinstance(seq, list):
        return ""
    for x in seq:
        if isinstance(x, str) and x.strip():
            return _truncate(x.strip(), max_len)
    return ""


def _resolve_post_id(platform: str, row: dict[str, Any]) -> Optional[str]:
    plat = (platform or "").strip().lower()
    if plat == "douyin":
        for key in ("aweme_id", "post_id", "item_id"):
            v = row.get(key)
            if v is not None and str(v).strip():
                return _truncate(str(v).strip(), 64)
        url = row.get("url")
        if isinstance(url, str) and "douyin.com" in url and "modal_id=" in url:
            m = _MODAL_ID_RE.search(url)
            if m:
                return _truncate(m.group(1), 64)
        return None
    if plat == "xhs":
        v = row.get("note_id") or row.get("post_id") or row.get("item_id")
        if v is not None and str(v).strip():
            return _truncate(str(v).strip(), 64)
        return None
    v = row.get("post_id")
    if v is not None and str(v).strip():
        return _truncate(str(v).strip(), 64)
    return None


def _douyin_row(
    r: dict[str, Any],
    *,
    task_id: Optional[int],
    user_id: str,
    keyword: str,
) -> dict[str, Any]:
    vlist = r.get("video_list")
    primary_video = _first_url(vlist, 256)
    cover = _truncate(str(r.get("cover") or ""), 256)
    return {
        "task_id": task_id,
        "user_id": _truncate(user_id, 64),
        "post_id": _truncate(str(r.get("aweme_id") or "").strip(), 64),
        "keyword": _truncate(keyword, 64),
        "nickname": _truncate(str(r.get("nickname") or ""), 64),
        "sec_uid": _truncate(str(r.get("user_id") or ""), 128),
        "content_type": _truncate("video", 16),
        "title": _truncate(str(r.get("title") or ""), 500),
        "summary": _truncate(str(r.get("desc") or ""), 65535),
        "page_url": _truncate(str(r.get("url") or ""), 512),
        "avatar_url": _truncate(str(r.get("avatar") or ""), 256),
        "author_signature": _truncate(str(r.get("signature") or ""), 256),
        "verify_name": _truncate(str(r.get("verify_name") or ""), 128),
        "cover_url": cover,
        "duration_seconds": int(round(float(r.get("duration") or 0))),
        "has_music": 0,
        "publish_time_ms": int(r.get("publish_time") or 0),
        "like_count": int(r.get("like_count") or 0),
        "comment_count": int(r.get("comment_count") or 0),
        "share_count": int(r.get("share_count") or 0),
        "collect_count": int(r.get("collect_count") or 0),
        "primary_image_url": cover,
        "primary_video_url": primary_video,
    }


def _xhs_row(
    r: dict[str, Any],
    *,
    task_id: Optional[int],
    user_id: str,
    keyword: str,
) -> dict[str, Any]:
    imgs = r.get("images_list")
    primary_image = _first_url(imgs, 256)
    primary_video = _first_url(r.get("video_list"), 256)
    cover = primary_image or _truncate(str(r.get("avatar") or ""), 256)
    return {
        "task_id": task_id,
        "user_id": _truncate(user_id, 64),
        "post_id": _truncate(str(r.get("note_id") or "").strip(), 64),
        "keyword": _truncate(keyword, 64),
        "nickname": _truncate(str(r.get("nickname") or ""), 64),
        "sec_uid": _truncate(str(r.get("userid") or ""), 128),
        "content_type": _truncate(str(r.get("content_type") or ""), 16),
        "title": _truncate(str(r.get("title") or ""), 500),
        "summary": _truncate(str(r.get("desc") or ""), 65535),
        "page_url": _truncate(str(r.get("url") or ""), 256),
        "xsec_token": _truncate(str(r.get("xsec_token") or ""), 64),
        "avatar_url": _truncate(str(r.get("avatar") or ""), 256),
        "author_signature": "",
        "verify_name": "",
        "cover_url": cover,
        "duration_seconds": int(r.get("duration") or 0),
        "has_music": 1 if r.get("has_music") else 0,
        "publish_time_ms": int(r.get("publish_time") or 0),
        "like_count": int(r.get("like_count") or 0),
        "comment_count": int(r.get("comment_count") or 0),
        "share_count": 0,
        "collect_count": int(r.get("collect_count") or 0),
        "primary_image_url": primary_image,
        "primary_video_url": primary_video,
    }


def _map_parsed_row(platform: str, r: dict[str, Any], *, task_id: Optional[int], user_id: str, keyword: str) -> dict[str, Any]:
    plat = (platform or "").strip().lower()
    if plat == "douyin":
        return _douyin_row(r, task_id=task_id, user_id=user_id, keyword=keyword)
    if plat == "xhs":
        return _xhs_row(r, task_id=task_id, user_id=user_id, keyword=keyword)
    raise ValueError(f"unsupported platform for row mapping: {platform!r}")


def _validate_mapped(m: dict[str, Any]) -> bool:
    return bool(m.get("post_id"))


def _normalize_rows(
    platform: str,
    keyword: str,
    results: Iterable[Any],
    task_id: Any,
    user_id: str,
) -> tuple[Type[Base], list[dict[str, Any]], int]:
    model = get_result_model(platform)
    uid = _truncate(user_id, 64)
    tid = _coerce_task_id_optional(task_id)
    kw = _truncate(keyword, 64)
    merged: dict[str, dict[str, Any]] = {}
    skipped = 0
    for raw in results:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        pid = _resolve_post_id(platform, raw)
        if not pid:
            skipped += 1
            continue
        try:
            m = _map_parsed_row(platform, raw, task_id=tid, user_id=uid, keyword=kw)
        except ValueError:
            skipped += 1
            continue
        m["post_id"] = pid
        if not _validate_mapped(m):
            skipped += 1
            continue
        merged[pid] = m
    return model, list(merged.values()), skipped


def _chunks(rows: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _insert_rows_fallback(session: Session, model: Type[Base], to_insert: list[dict[str, Any]]) -> tuple[int, int, int]:
    inserted = 0
    duplicated = 0
    persist_errors = 0
    for m in to_insert:
        try:
            with session.begin_nested():
                session.bulk_insert_mappings(model, [m])
            inserted += 1
        except IntegrityError:
            duplicated += 1
        except Exception:
            persist_errors += 1
            logger.warning("skip row insert model=%s keys=%s", model.__name__, list(m.keys())[:8], exc_info=True)
    return inserted, duplicated, persist_errors


def save_search_results(
    platform: str,
    keyword: str,
    results: Iterable[Any],
    *,
    user_id: str,
    task_id: Any = None,
) -> dict[str, int]:
    """
    将解析后的搜索结果批量写入对应平台结果表；按 post_id 全局去重（单表内唯一）。

    :return: inserted、duplicated、skipped、persist_errors
    """
    if not get_settings().database_url.strip():
        raise RuntimeError("DATABASE_URL is not configured")
    if not (user_id or "").strip():
        raise ValueError("user_id is required for save_search_results")

    model, rows, skipped_total = _normalize_rows(platform, keyword, results, task_id, user_id.strip())
    inserted_total = 0
    duplicated_total = 0
    persist_errors_total = 0

    if not rows:
        return {"inserted": 0, "duplicated": 0, "skipped": skipped_total, "persist_errors": 0}

    post_id_col = getattr(model, "post_id")

    for chunk in _chunks(rows, _BATCH_SIZE):
        with session_scope() as session:
            pids = [str(r["post_id"]) for r in chunk]
            stmt = select(post_id_col).where(post_id_col.in_(pids))
            existing_ids = set(session.execute(stmt).scalars().all())

            to_insert: list[dict[str, Any]] = []
            for r in chunk:
                pid = str(r["post_id"])
                if pid in existing_ids:
                    duplicated_total += 1
                else:
                    to_insert.append(r)
                    existing_ids.add(pid)

            if not to_insert:
                continue

            try:
                session.bulk_insert_mappings(model, to_insert)
                session.flush()
                inserted_total += len(to_insert)
            except Exception as e:
                session.rollback()
                if isinstance(e, IntegrityError):
                    logger.info("bulk insert integrity conflict, row-wise retry batch_size=%s", len(to_insert))
                else:
                    logger.exception("bulk_insert_mappings failed, falling back to row-wise inserts")
                ins, dup, perr = _insert_rows_fallback(session, model, to_insert)
                inserted_total += ins
                duplicated_total += dup
                persist_errors_total += perr

    return {
        "inserted": inserted_total,
        "duplicated": duplicated_total,
        "skipped": skipped_total,
        "persist_errors": persist_errors_total,
    }


def _model_to_item(obj: Base) -> dict[str, Any]:
    d: dict[str, Any] = {}
    for col in obj.__table__.columns:
        v = getattr(obj, col.key, None)
        if isinstance(v, datetime):
            d[col.key] = v.isoformat()
        else:
            d[col.key] = v
    return d


def paginate_task_results(
    session: Session,
    *,
    platform: str,
    task_id: int,
    page: int,
    limit: int,
    user_id: Optional[str] = None,
    is_upload: Optional[int] = None,
) -> tuple[int, list[dict[str, Any]]]:
    """
    按任务分页查询平台结果表；可选按 user_id / is_upload 过滤。
    page 从 1 开始。
    """
    model = get_result_model(platform)
    tid_col = getattr(model, "task_id")
    uid_col = getattr(model, "user_id")
    upload_col = getattr(model, "is_upload")
    ct_col = getattr(model, "create_time")

    filters = [tid_col == task_id]
    if user_id is not None and str(user_id).strip():
        filters.append(uid_col == str(user_id).strip())
    if is_upload is not None:
        filters.append(upload_col == int(is_upload))

    count_stmt = select(func.count()).select_from(model).where(*filters)
    total = int(session.execute(count_stmt).scalar_one())

    offset = max(0, (page - 1) * limit)
    list_stmt = select(model).where(*filters).order_by(ct_col.desc()).offset(offset).limit(limit)
    rows = session.execute(list_stmt).scalars().all()
    return total, [_model_to_item(r) for r in rows]
