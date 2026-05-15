"""异步任务 `body` 的 Pydantic 模型（与 `http_sync_bodies` 搜索字段对齐，便于校验）。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class DouyinSearchDetailBody(BaseModel):
    post_id: str = Field(..., min_length=1, max_length=64, description="抖音作品 ID（aweme_id）")


class XhsSearchDetailBody(BaseModel):
    post_id: str = Field(..., min_length=1, max_length=64, description="小红书笔记 ID（note_id）")
