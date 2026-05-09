"""
飞书插件任务配置：列表、详情、创建、更新。
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
    """分页查询任务配置列表（按 id 倒序）。"""
    try:
        rows = feishu_task_config_service.list_feishu_task_configs(db, skip=skip, limit=limit)
        items = [FeishuTaskConfigListItemOut.model_validate(r) for r in rows]
        return ApiResponse.success(data=items, message="查询成功")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=_detail_from_sqlalchemy(e)) from None


@router.get("/feishu-task-configs/{config_id}")
def get_feishu_task_config(
    config_id: int, db: Session = Depends(get_db)
) -> ApiResponse[FeishuTaskConfigDetailOut]:
    """按 id 查询单条任务配置（含 config JSON）。"""
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
    """新建一条任务配置。"""
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
    """全量更新指定 id 的任务配置。"""
    try:
        row = feishu_task_config_service.update_feishu_task_config(db, config_id, config=body.config)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=_detail_from_sqlalchemy(e)) from None
    if row is None:
        raise HTTPException(status_code=404, detail="任务配置不存在")
    return ApiResponse.success(data=FeishuTaskConfigIdOut(id=row.id), message="保存成功")
