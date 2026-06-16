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

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config.settings import get_settings
from social_platform.database.session import session_scope
from social_platform.models.base import Base
from social_platform.models.results.registry import get_result_model, list_supported_platforms

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500
# 结果 API 不返回的基层列（各平台业务列原样透出，由 meta.platform 区分）
_RESULT_API_EXCLUDE_COLUMNS = frozenset(
    {"id", "task_id", "user_id", "create_time", "update_time"}
)
_MODAL_ID_RE = re.compile(r"modal_id=(\d+)", re.IGNORECASE)
_RESULT_REF_SEP = ":"
_SUPPORTED_PLATFORMS = frozenset(list_supported_platforms())


def encode_result_ref(platform: str, row_id: int) -> str:
    """跨平台唯一结果引用：``{platform}:{表主键 id}``。"""
    plat = (platform or "").strip().lower()
    if plat not in _SUPPORTED_PLATFORMS:
        raise ValueError(f"unsupported platform: {platform!r}")
    return f"{plat}{_RESULT_REF_SEP}{int(row_id)}"


def parse_result_ref(ref: str) -> tuple[str, int]:
    """解析 ``encode_result_ref`` 生成的引用。"""
    raw = (ref or "").strip()
    if _RESULT_REF_SEP not in raw:
        raise ValueError(f"invalid result ref: {ref!r}")
    plat, _, id_part = raw.partition(_RESULT_REF_SEP)
    plat = plat.strip().lower()
    if plat not in _SUPPORTED_PLATFORMS:
        raise ValueError(f"unsupported platform in ref: {ref!r}")
    try:
        row_id = int(id_part.strip())
    except (TypeError, ValueError) as e:
        raise ValueError(f"invalid result id in ref: {ref!r}") from e
    if row_id <= 0:
        raise ValueError(f"invalid result id in ref: {ref!r}")
    return plat, row_id


def list_pending_result_row_ids(
    session: Session,
    *,
    platform: str,
    user_id: Optional[str] = None,
    task_id: Optional[int] = None,
) -> list[int]:
    """
    查询某平台 ``is_upload=0`` 的结果表主键列表。
    ``task_id=None`` 不按任务过滤（含同步单次执行 ``task_id IS NULL`` 的行）。
    """
    model = get_result_model(platform)
    tid_col = getattr(model, "task_id")
    uid_col = getattr(model, "user_id")
    upload_col = getattr(model, "is_upload")
    id_col = getattr(model, "id")

    filters = [upload_col == 0]
    if task_id is not None:
        filters.append(tid_col == int(task_id))
    if user_id is not None and str(user_id).strip():
        filters.append(uid_col == str(user_id).strip())

    stmt = select(id_col).where(*filters).order_by(id_col.asc())
    return [int(r) for r in session.execute(stmt).scalars().all()]


def mark_results_uploaded(
    session: Session,
    *,
    platform: str,
    row_ids: Iterable[int],
    user_id: Optional[str] = None,
    task_id: Optional[int] = None,
) -> int:
    """
    将指定主键行的 ``is_upload`` 置为 1（仅更新当前仍为 0 的行）。
    ``task_id=None`` 时不限制任务（可验收同步单次写入、无 task_id 的行）。
    """
    ids = sorted({int(i) for i in row_ids if int(i) > 0})
    if not ids:
        return 0
    model = get_result_model(platform)
    tid_col = getattr(model, "task_id")
    uid_col = getattr(model, "user_id")
    upload_col = getattr(model, "is_upload")
    id_col = getattr(model, "id")

    filters = [upload_col == 0, id_col.in_(ids)]
    if task_id is not None:
        filters.append(tid_col == int(task_id))
    if user_id is not None and str(user_id).strip():
        filters.append(uid_col == str(user_id).strip())

    stmt = update(model).where(*filters).values(is_upload=1)
    result = session.execute(stmt)
    return int(result.rowcount or 0)


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


def _wxvideo_row(
    r: dict[str, Any],
    *,
    task_id: Optional[int],
    user_id: str,
    keyword: str,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "user_id": _truncate(user_id, 64),
        "post_id": _truncate(str(r.get("post_id") or "").strip(), 64),
        "keyword": _truncate(keyword, 64),
        "nickname": _truncate(str(r.get("nickname") or ""), 64),
        "avatar_url": _truncate(str(r.get("avatar_url") or ""), 256),
        "title": _truncate(str(r.get("title") or ""), 500),
        "publish_time": int(r.get("publish_time") or 0),
        "duration": int(r.get("duration") or 0),
        "cover_url": _truncate(str(r.get("cover_url") or ""), 512),
        "video_url": _truncate(str(r.get("video_url") or ""), 512),
        "like_count": int(r.get("like_count") or 0),
        "comment_count": int(r.get("comment_count") or 0),
        "forward_count": int(r.get("forward_count") or 0),
        "thumb_count": int(r.get("thumb_count") or 0),
    }


def _mp_row(
    r: dict[str, Any],
    *,
    task_id: Optional[int],
    user_id: str,
    keyword: str,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "user_id": _truncate(user_id, 64),
        "post_id": _truncate(
            str(r.get("post_id") or r.get("article_id") or "").strip(), 64
        ),
        "keyword": _truncate(keyword, 64),
        "company_name": _truncate(str(r.get("company_name") or ""), 128),
        "biz": _truncate(str(r.get("biz") or ""), 64),
        "title": _truncate(str(r.get("title") or ""), 500),
        "summary": _truncate(str(r.get("summary") or r.get("content") or ""), 65535),
        "url": _truncate(str(r.get("url") or ""), 512),
        "avatar_url": _truncate(str(r.get("avatar_url") or ""), 256),
        "publish_time": int(r.get("publish_time") or 0),
    }


def _map_parsed_row(
    platform: str,
    r: dict[str, Any],
    *,
    task_id: Optional[int],
    user_id: str,
    keyword: str,
) -> dict[str, Any]:
    plat = (platform or "").strip().lower()
    if plat == "douyin":
        return _douyin_row(r, task_id=task_id, user_id=user_id, keyword=keyword)
    if plat == "xhs":
        return _xhs_row(r, task_id=task_id, user_id=user_id, keyword=keyword)
    if plat == "wxvideo":
        return _wxvideo_row(r, task_id=task_id, user_id=user_id, keyword=keyword)
    if plat == "mp":
        return _mp_row(r, task_id=task_id, user_id=user_id, keyword=keyword)
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


def _existing_post_ids_in_task_scope(
    session: Session,
    model: Type[Base],
    *,
    task_id: Optional[int],
    post_ids: list[str],
) -> set[str]:
    """同一 ``task_id`` 作用域内已存在的 ``post_id``（``task_id=None`` 仅查同步无任务行）。"""
    if not post_ids:
        return set()
    post_id_col = getattr(model, "post_id")
    task_id_col = getattr(model, "task_id")
    filters = [post_id_col.in_(post_ids)]
    if task_id is not None:
        filters.append(task_id_col == task_id)
    else:
        filters.append(task_id_col.is_(None))
    stmt = select(post_id_col).where(*filters)
    return {str(x) for x in session.execute(stmt).scalars().all()}


def _chunks(rows: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _insert_rows_fallback(
    session: Session, model: Type[Base], to_insert: list[dict[str, Any]]
) -> tuple[int, int, int, list[dict[str, Any]]]:
    inserted = 0
    duplicated = 0
    persist_errors = 0
    row_results: list[dict[str, Any]] = []
    for m in to_insert:
        pid = str(m.get("post_id") or "")
        try:
            with session.begin_nested():
                session.bulk_insert_mappings(model, [m])
            inserted += 1
            row_results.append(
                {"post_id": pid, "save_result": True, "reason": "inserted"}
            )
        except IntegrityError:
            duplicated += 1
            row_results.append(
                {"post_id": pid, "save_result": False, "reason": "duplicate"}
            )
            logger.info("skip duplicate row post_id=%s model=%s", pid, model.__name__)
            logger.info(
                "duplicate skipped",
                extra={
                    "platform": model.__tablename__,
                    "duplicated_count": 1,
                    "post_id": pid,
                },
            )
        except Exception:
            persist_errors += 1
            row_results.append(
                {"post_id": pid, "save_result": False, "reason": "persist_error"}
            )
            logger.warning(
                "skip row insert model=%s keys=%s",
                model.__name__,
                list(m.keys())[:8],
                exc_info=True,
            )
    return inserted, duplicated, persist_errors, row_results


def save_search_results(
    platform: str,
    keyword: str,
    results: Iterable[Any],
    *,
    user_id: str,
    task_id: Any = None,
) -> dict[str, Any]:
    """
    将解析后的搜索结果批量写入对应平台结果表；按 (task_id, post_id) 任务内去重。

    :return: 统一统计字段 inserted_count/duplicated_count/failed_count + row_results
    """
    if not get_settings().database_url.strip():
        raise RuntimeError("DATABASE_URL is not configured")
    if not (user_id or "").strip():
        raise ValueError("user_id is required for save_search_results")

    scoped_task_id = _coerce_task_id_optional(task_id)
    model, rows, skipped_total = _normalize_rows(
        platform, keyword, results, task_id, user_id.strip()
    )
    inserted_total = 0
    duplicated_total = 0
    persist_errors_total = 0
    row_results: list[dict[str, Any]] = []

    if not rows:
        return {
            "inserted_count": 0,
            "duplicated_count": 0,
            "failed_count": 0,
            "skipped_count": skipped_total,
            "inserted": 0,
            "duplicated": 0,
            "skipped": skipped_total,
            "persist_errors": 0,
            "row_results": [],
        }

    for chunk in _chunks(rows, _BATCH_SIZE):
        with session_scope() as session:
            pids = [str(r["post_id"]) for r in chunk]
            existing_ids = _existing_post_ids_in_task_scope(
                session,
                model,
                task_id=scoped_task_id,
                post_ids=pids,
            )

            to_insert: list[dict[str, Any]] = []
            for r in chunk:
                pid = str(r["post_id"])
                if pid in existing_ids:
                    duplicated_total += 1
                    row_results.append(
                        {
                            "post_id": pid,
                            "save_result": False,
                            "reason": "duplicate",
                        }
                    )
                    logger.info(
                        "skip duplicate row post_id=%s task_id=%s model=%s",
                        pid,
                        scoped_task_id,
                        model.__name__,
                    )
                    logger.info(
                        "duplicate skipped",
                        extra={
                            "platform": (platform or "").strip().lower(),
                            "task_id": scoped_task_id,
                            "duplicated_count": 1,
                            "post_id": pid,
                        },
                    )
                else:
                    to_insert.append(r)
                    existing_ids.add(pid)

            if not to_insert:
                continue

            try:
                session.bulk_insert_mappings(model, to_insert)
                session.flush()
                inserted_total += len(to_insert)
                row_results.extend(
                    {
                        "post_id": str(r.get("post_id") or ""),
                        "save_result": True,
                        "reason": "inserted",
                    }
                    for r in to_insert
                )
            except Exception as e:
                session.rollback()
                if isinstance(e, IntegrityError):
                    logger.info(
                        "bulk insert integrity conflict, row-wise retry batch_size=%s",
                        len(to_insert),
                    )
                else:
                    logger.exception(
                        "bulk_insert_mappings failed, falling back to row-wise inserts"
                    )
                ins, dup, perr, details = _insert_rows_fallback(session, model, to_insert)
                inserted_total += ins
                duplicated_total += dup
                persist_errors_total += perr
                row_results.extend(details)

    return {
        "inserted_count": inserted_total,
        "duplicated_count": duplicated_total,
        "failed_count": persist_errors_total,
        "skipped_count": skipped_total,
        "inserted": inserted_total,
        "duplicated": duplicated_total,
        "skipped": skipped_total,
        "persist_errors": persist_errors_total,
        "row_results": row_results,
    }


def _model_to_result_item(obj: Base, *, platform: str = "") -> dict[str, Any]:
    """按 ORM 列名序列化单条结果；排除基层字段，不做跨平台字段映射。"""
    d: dict[str, Any] = {}
    for col in obj.__table__.columns:
        if col.key in _RESULT_API_EXCLUDE_COLUMNS:
            continue
        v = getattr(obj, col.key, None)
        if isinstance(v, datetime):
            d[col.key] = v.isoformat()
        else:
            d[col.key] = v
    plat = (platform or "").strip().lower()
    row_id = getattr(obj, "id", None)
    if plat and row_id is not None:
        d["result_ref"] = encode_result_ref(plat, int(row_id))
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
    list_stmt = (
        select(model)
        .where(*filters)
        .order_by(ct_col.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = session.execute(list_stmt).scalars().all()
    plat_key = (platform or "").strip().lower()
    return total, [_model_to_result_item(r, platform=plat_key) for r in rows]


def list_pending_acceptance_by_platform(
    session: Session,
    *,
    user_id: Optional[str] = None,
) -> tuple[dict[str, list[int]], int]:
    """
    四平台待验收（``is_upload=0``）主键，按平台分组。
    含异步任务与同步单次执行（``task_id`` 可为 NULL）的数据。
    """
    by_platform: dict[str, list[int]] = {}
    for plat in list_supported_platforms():
        row_ids = list_pending_result_row_ids(
            session, platform=plat, user_id=user_id, task_id=None
        )
        if row_ids:
            by_platform[plat] = row_ids
    total = sum(len(v) for v in by_platform.values())
    return by_platform, total


def accept_results_by_platform(
    session: Session,
    *,
    by_platform: dict[str, Iterable[int]],
    user_id: Optional[str] = None,
) -> dict[str, int]:
    """批量验收：``{ platform: [row_id, ...] }``，返回各平台实际更新行数。"""
    updated: dict[str, int] = {}
    for plat_raw, row_ids in (by_platform or {}).items():
        plat = (plat_raw or "").strip().lower()
        if plat not in _SUPPORTED_PLATFORMS:
            raise ValueError(f"unsupported platform: {plat_raw!r}")
        updated[plat] = mark_results_uploaded(
            session,
            platform=plat,
            row_ids=row_ids,
            user_id=user_id,
            task_id=None,
        )
    return updated
