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


class FeishuTaskConfigWriteOut(BaseModel):
    """POST/PUT 成功后返回：便于前端立即展示服务端计算的卡片状态（不依赖列表 GET 是否含 `display_status`）。"""

    id: int
    display_status: str = Field(
        ...,
        description="保存后根据入库 config 与当前时间计算的卡片状态：`running`|`stopped`|`pending_run`|`completed`|`failed`。",
    )
    stopped_kind: Optional[str] = Field(
        default=None,
        description="当 display_status 为 stopped 时的子类；否则 null。",
    )


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
    expire_at: Optional[str] = Field(
        default=None,
        description="表单 `expireAt` 原始字符串。",
    )
    task_paused: Optional[bool] = Field(
        default=None,
        description="表单 `taskPaused`：窗口内用户点击「停止」后为 true；缺省为 null（视为 false）。",
    )
    task_abnormal: Optional[bool] = Field(
        default=None,
        description="表单 `taskAbnormal`：任务异常（如外部接口调用失败）后为 true；前端与 `run_status=failed` 一并视为失败态。",
    )
    run_status: Optional[str] = Field(
        default=None,
        description="表单 `runStatus`：失败时可写 `failed`；亦可用 `taskAbnormal` 表示异常。",
    )
    display_status: str = Field(
        ...,
        description="服务端根据 config 与当前时间计算的卡片状态：`running`|`stopped`|`pending_run`|`completed`|`failed`。",
    )
    stopped_kind: Optional[str] = Field(
        default=None,
        description="当 display_status 为 `stopped` 时：`before_effective`|`paused_in_window`|`neutral`；否则 null。",
    )


class FeishuTaskConfigDetailOut(BaseModel):
    """详情接口 `GET /api/feishu-task-configs/{id}` 的 `data` 载荷。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_name: Optional[str] = None
    config: dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    display_status: str = Field(
        ...,
        description="与列表一致：服务端根据 config 与当前时间计算的卡片状态（含 `pending_run`）。",
    )
    stopped_kind: Optional[str] = Field(
        default=None,
        description="与列表一致：`stopped` 时的子类，否则 null。",
    )
