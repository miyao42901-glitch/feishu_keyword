"""同步接口 POST JSON 体：业务字段（与下游第三方 body 一致）；`X-API-Key` 仅通过 Header 传递。"""
from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field


class SyncSearchJsonBody(BaseModel):
    keyword: str = Field(..., min_length=1)
    cursor: str = ""
    log_id: str = Field(default="", validation_alias=AliasChoices("log_id", "logid"))
    sort_type: str = ""
    publish_time: str = ""
    filter_duration: str = ""
    content_type: str = ""


class DouyinSearchPageBody(SyncSearchJsonBody):
    pass


class DouyinSearchAllBody(SyncSearchJsonBody):
    max_pages: int = Field(default=10, ge=1, le=50)


class XhsSearchPageBody(SyncSearchJsonBody):
    pass


class XhsSearchAllBody(SyncSearchJsonBody):
    max_pages: int = Field(default=10, ge=1, le=50)
