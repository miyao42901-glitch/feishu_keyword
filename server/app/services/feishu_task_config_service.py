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


def task_paused_from_config(cfg: dict[str, Any]) -> bool:
    """
    从 config_json 解析「窗口内用户点击停止」标记。

    列表接口曾仅用 `isinstance(v, bool)`，若历史数据或序列化把 true/false 写成字符串/数字，
    会得到 `null`，前端 `task_paused === true` 恒为假，表现为点击停止后仍显示运行中。
    """
    for key in ("taskPaused", "task_paused"):
        if key not in cfg:
            continue
        v = cfg[key]
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("true", "1", "yes", "on"):
                return True
            if s in ("false", "0", "no", "off", ""):
                return False
        if isinstance(v, (int, float)):
            if v == 1:
                return True
            if v == 0:
                return False
    return False


def normalize_config_for_storage(config: dict[str, Any]) -> dict[str, Any]:
    """写入前统一 `taskPaused` 等布尔字段为严格 bool，便于列表解析与前端判断。"""
    out = dict(config)
    out["taskPaused"] = task_paused_from_config(out)
    return out


def list_feishu_task_configs(db: Session, *, skip: int = 0, limit: int = 100) -> List[FeishuTaskConfig]:
    safe_limit = min(limit, MAX_LIST_LIMIT)
    stmt = select(FeishuTaskConfig).order_by(FeishuTaskConfig.id.desc()).offset(skip).limit(safe_limit)
    return list(db.scalars(stmt).all())


def get_feishu_task_config(db: Session, config_id: int) -> Optional[FeishuTaskConfig]:
    return db.get(FeishuTaskConfig, config_id)


def create_feishu_task_config(db: Session, *, config: dict[str, Any]) -> FeishuTaskConfig:
    normalized = normalize_config_for_storage(config)
    row = FeishuTaskConfig(
        plan_name=_plan_name_from_config(normalized),
        config_json=json.dumps(normalized, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_feishu_task_config(db: Session, config_id: int, *, config: dict[str, Any]) -> Optional[FeishuTaskConfig]:
    row = db.get(FeishuTaskConfig, config_id)
    if row is None:
        return None
    normalized = normalize_config_for_storage(config)
    row.plan_name = _plan_name_from_config(normalized)
    row.config_json = json.dumps(normalized, ensure_ascii=False)
    db.commit()
    db.refresh(row)
    return row


def delete_feishu_task_config(db: Session, config_id: int) -> bool:
    """按主键删除一行；不存在则返回 False。"""
    row = db.get(FeishuTaskConfig, config_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def config_dict_from_row(row: FeishuTaskConfig) -> dict[str, Any]:
    try:
        data = json.loads(row.config_json or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}
