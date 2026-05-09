"""
飞书插件任务配置 HTTP 接口。

路径均挂在 `/api` 下（见 `app.api.router`）。读写表 `feishu_task_configs`，
成功响应为统一信封 `ApiResponse`（`docs/API.md` 第五节）；数据库异常映射为 HTTP 503 + 业务码。

对应前端封装：`feishu/src/lib/api.ts`（`listFeishuTaskConfigs` 等）。
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import DEFAULT_LIST_LIMIT
from app.schemas.api_response import ApiResponse
from app.schemas.feishu_task_config import (
    FeishuTaskConfigDetailOut,
    FeishuTaskConfigIdOut,
    FeishuTaskConfigListItemOut,
    FeishuTaskConfigUpsertBody,
)
from app.services import feishu_task_config_service

router = APIRouter()
logger = logging.getLogger(__name__)

_DB_HINT = (
    "数据库操作失败：请确认已在 MySQL 创建表 feishu_task_configs。"
    " 可在 server 目录执行：python scripts/ensure_feishu_task_configs_table.py"
    "（需配置 server/.env 中 DATABASE_URL）；或手动执行 server/scripts/create_feishu_task_configs.sql。"
    " 并检查 DATABASE_URL 能否连接库 feishu_keyword。"
)


def _detail_from_sqlalchemy(exc: SQLAlchemyError) -> str:
    """将 SQLAlchemy 异常压缩为适合放入 HTTP `detail` / 统一 `message` 的短文案（含建表提示）。"""
    inner = getattr(exc, "orig", None)
    raw = str(inner).strip() if inner is not None else str(exc).strip()
    logger.warning("feishu_task_configs DB error: %s", raw)
    if len(raw) > 320:
        raw = raw[:320] + "…"
    return f"{_DB_HINT} 【原因】{raw}"


@router.get("/feishu-task-configs")
def list_feishu_task_configs(
    skip: int = 0,
    limit: int = DEFAULT_LIST_LIMIT,
    db: Session = Depends(get_db),
) -> ApiResponse[List[FeishuTaskConfigListItemOut]]:
    """
    分页查询任务配置列表。

    路径：`GET /api/feishu-task-configs`。

    Args:
        skip: 偏移量，默认 0。
        limit: 每页条数，默认 `DEFAULT_LIST_LIMIT`，服务端裁剪不超过 `MAX_LIST_LIMIT`。
        db: 请求级会话，由 `get_db` 注入。

    Returns:
        `code=0` 时 `data` 为列表项数组（`id`、`plan_name`、`updated_at` 及从 `config` 解析的
        `task_type`、`platform_keys`、`effective_at`），按 `id` 降序。

    Raises:
        HTTPException: 503 — 数据库错误，`detail` 含排查说明与 MySQL 摘要。
    """
    try:
        rows = feishu_task_config_service.list_feishu_task_configs(db, skip=skip, limit=limit)
        items: List[FeishuTaskConfigListItemOut] = []
        for r in rows:
            cfg = feishu_task_config_service.config_dict_from_row(r)
            tt = cfg.get("taskType")
            task_type = tt if tt in ("scheduled", "realtime") else None
            raw_sources = cfg.get("selectedSources")
            platform_keys: list[str] | None = None
            if isinstance(raw_sources, list):
                platform_keys = [str(x) for x in raw_sources if x is not None]
            eff = cfg.get("effectiveAt")
            effective_at = str(eff).strip() if eff is not None and str(eff).strip() else None
            items.append(
                FeishuTaskConfigListItemOut(
                    id=r.id,
                    plan_name=r.plan_name,
                    updated_at=r.updated_at,
                    task_type=task_type,
                    platform_keys=platform_keys,
                    effective_at=effective_at,
                )
            )
        return ApiResponse.success(data=items, message="查询成功")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=_detail_from_sqlalchemy(e)) from None


@router.get("/feishu-task-configs/{config_id}")
def get_feishu_task_config(
    config_id: int, db: Session = Depends(get_db)
) -> ApiResponse[FeishuTaskConfigDetailOut]:
    """
    按主键查询单条任务配置（含完整 `config` 对象）。

    路径：`GET /api/feishu-task-configs/{config_id}`。

    Args:
        config_id: `feishu_task_configs.id`。
        db: 请求级会话。

    Returns:
        `code=0` 时 `data` 为 `FeishuTaskConfigDetailOut`（含 `config` 字典）。

    Raises:
        HTTPException: 404 — 记录不存在；503 — 数据库错误。
    """
    try:
        row = feishu_task_config_service.get_feishu_task_config(db, config_id)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=_detail_from_sqlalchemy(e)) from None
    if row is None:
        raise HTTPException(status_code=404, detail="任务配置不存在")
    payload = FeishuTaskConfigDetailOut(
        id=row.id,
        plan_name=row.plan_name,
        config=feishu_task_config_service.config_dict_from_row(row),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    return ApiResponse.success(data=payload, message="查询成功")


@router.post("/feishu-task-configs")
def create_feishu_task_config(
    body: FeishuTaskConfigUpsertBody, db: Session = Depends(get_db)
) -> ApiResponse[FeishuTaskConfigIdOut]:
    """
    新建一条任务配置（插入一行，`config` 序列化为 `config_json`）。

    路径：`POST /api/feishu-task-configs`。

    Args:
        body: 请求体 `FeishuTaskConfigUpsertBody`，字段 `config` 为前端表单快照。
        db: 请求级会话。

    Returns:
        `code=0` 时 `data` 为 `{ "id": 新主键 }`。

    Raises:
        HTTPException: 503 — 数据库错误（常见：表未创建）。
    """
    try:
        row = feishu_task_config_service.create_feishu_task_config(db, config=body.config)
        return ApiResponse.success(data=FeishuTaskConfigIdOut(id=row.id), message="保存成功")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=_detail_from_sqlalchemy(e)) from None


@router.put("/feishu-task-configs/{config_id}")
def update_feishu_task_config(
    config_id: int,
    body: FeishuTaskConfigUpsertBody,
    db: Session = Depends(get_db),
) -> ApiResponse[FeishuTaskConfigIdOut]:
    """
    全量更新指定 id 的任务配置（覆盖 `plan_name` 与 `config_json`）。

    路径：`PUT /api/feishu-task-configs/{config_id}`。

    Args:
        config_id: 要更新的主键。
        body: 与创建相同，`config` 为完整快照。
        db: 请求级会话。

    Returns:
        `code=0` 时 `data` 为 `{ "id": config_id }`。

    Raises:
        HTTPException: 404 — 记录不存在；503 — 数据库错误。
    """
    try:
        row = feishu_task_config_service.update_feishu_task_config(db, config_id, config=body.config)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=_detail_from_sqlalchemy(e)) from None
    if row is None:
        raise HTTPException(status_code=404, detail="任务配置不存在")
    return ApiResponse.success(data=FeishuTaskConfigIdOut(id=row.id), message="保存成功")


@router.delete("/feishu-task-configs/{config_id}")
def delete_feishu_task_config(
    config_id: int, db: Session = Depends(get_db)
) -> ApiResponse[FeishuTaskConfigIdOut]:
    """
    删除指定 id 的任务配置。

    路径：`DELETE /api/feishu-task-configs/{config_id}`。

    Args:
        config_id: 要删除的主键。
        db: 请求级会话。

    Returns:
        `code=0` 时 `data` 为 `{ "id": config_id }`。

    Raises:
        HTTPException: 404 — 记录不存在；503 — 数据库错误。
    """
    try:
        ok = feishu_task_config_service.delete_feishu_task_config(db, config_id)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=_detail_from_sqlalchemy(e)) from None
    if not ok:
        raise HTTPException(status_code=404, detail="任务配置不存在")
    return ApiResponse.success(data=FeishuTaskConfigIdOut(id=config_id), message="删除成功")
