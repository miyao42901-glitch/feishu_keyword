"""
飞书插件任务配置（feishu_task_configs）的查询与写入。
"""

from __future__ import annotations

import json
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import MAX_LIST_LIMIT
from app.models import FeishuTaskConfig


def _plan_name_from_config(config: dict[str, Any]) -> Optional[str]:
    name = config.get("planName")
    if name is None:
        return None
    s = str(name).strip()
    return s or None


def list_feishu_task_configs(db: Session, *, skip: int = 0, limit: int = 100) -> List[FeishuTaskConfig]:
    safe_limit = min(limit, MAX_LIST_LIMIT)
    stmt = select(FeishuTaskConfig).order_by(FeishuTaskConfig.id.desc()).offset(skip).limit(safe_limit)
    return list(db.scalars(stmt).all())


def get_feishu_task_config(db: Session, config_id: int) -> Optional[FeishuTaskConfig]:
    return db.get(FeishuTaskConfig, config_id)


def create_feishu_task_config(db: Session, *, config: dict[str, Any]) -> FeishuTaskConfig:
    row = FeishuTaskConfig(
        plan_name=_plan_name_from_config(config),
        config_json=json.dumps(config, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_feishu_task_config(db: Session, config_id: int, *, config: dict[str, Any]) -> Optional[FeishuTaskConfig]:
    row = db.get(FeishuTaskConfig, config_id)
    if row is None:
        return None
    row.plan_name = _plan_name_from_config(config)
    row.config_json = json.dumps(config, ensure_ascii=False)
    db.commit()
    db.refresh(row)
    return row


def config_dict_from_row(row: FeishuTaskConfig) -> dict[str, Any]:
    try:
        data = json.loads(row.config_json or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}
