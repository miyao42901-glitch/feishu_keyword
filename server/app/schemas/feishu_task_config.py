"""
飞书插件任务配置 API 的 Pydantic 模型。

`config` 为前端表单快照（JSON 对象），字段随产品迭代扩展；服务端原样序列化入库。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class FeishuTaskConfigUpsertBody(BaseModel):
    """
    创建（POST）或全量更新（PUT）时的 JSON 请求体。

    对应路由：`POST|PUT /api/feishu-task-configs`（及带 id 的 PUT）。
    """

    config: dict[str, Any] = Field(
        ...,
        description="任务配置 JSON，与前端表单结构一致；含授权码等敏感字段，生产环境建议改为独立密钥表或加密存储。",
    )


class FeishuTaskConfigIdOut(BaseModel):
    """写入成功后，统一响应 `data` 内仅含新 id 或已更新 id。"""

    id: int


class FeishuTaskConfigListItemOut(BaseModel):
    """
    列表接口 `GET /api/feishu-task-configs` 单条 `data` 元素。

    `task_type`、`platform_keys`、`effective_at` 由服务端从 `config_json` 解析，供列表卡片展示；
    缺省或无法解析时为 `null`。
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    task_type: Optional[str] = Field(
        default=None,
        description="表单 `taskType`：`scheduled` | `realtime`。",
    )
    platform_keys: Optional[list[str]] = Field(
        default=None,
        description="表单 `selectedSources`：平台 id 列表。",
    )
    effective_at: Optional[str] = Field(
        default=None,
        description="表单 `effectiveAt` 原始字符串（多为日期时间）。",
    )


class FeishuTaskConfigDetailOut(BaseModel):
    """详情接口 `GET /api/feishu-task-configs/{id}` 的 `data` 载荷。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_name: Optional[str] = None
    config: dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
