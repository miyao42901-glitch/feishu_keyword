"""
飞书插件任务配置 API 的 Pydantic 模型。

`config` 为前端表单快照（JSON 对象），字段随产品迭代扩展；服务端原样序列化入库。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class FeishuTaskConfigUpsertBody(BaseModel):
    """创建或全量更新时的请求体。"""

    config: dict[str, Any] = Field(
        ...,
        description="任务配置 JSON，与前端表单结构一致；含授权码等敏感字段，生产环境建议改为独立密钥表或加密存储。",
    )


class FeishuTaskConfigIdOut(BaseModel):
    """写入成功后返回主键。"""

    id: int


class FeishuTaskConfigListItemOut(BaseModel):
    """列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_name: Optional[str] = None
    updated_at: Optional[datetime] = None


class FeishuTaskConfigDetailOut(BaseModel):
    """详情（含完整 config）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_name: Optional[str] = None
    config: dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
