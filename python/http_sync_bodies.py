"""同步接口 POST JSON 体：业务字段（与下游第三方 body 一致）；`X-API-Key` 仅通过 Header 传递。"""
from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field


class PublicSearchAllBody(BaseModel):
    """search-all 专用：多页采集控制字段。"""

    exclude_words: str = Field(default="", description="排除词，空格分隔")
    fetch_count: int = Field(
        default=100,
        ge=1,
        le=500,
        description="采集条数上限；达到或时间窗内无更多数据即停",
    )
    time_range: int = Field(
        default=7,
        ge=1,
        description="时间范围（天）；仅 sort_type=2 时参与时间窗与第三方 days 映射",
    )
    sort_type: int = Field(
        default=1,
        ge=0,
        le=2,
        description="0 占位/默认排序；1 按相关性；2 按时间（为 2 时 time_range 才生效）",
    )


class DouyinSearchPageBody(BaseModel):
    """抖音单页搜索（与第三方检索参数一致）。"""

    keyword: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="搜索关键词，1-100 字，支持多关键词",
    )
    cursor: str = Field(default="", description="翻页；首页留空，后续用上一页返回的 cursor")
    log_id: str = Field(
        default="",
        validation_alias=AliasChoices("log_id", "logid"),
        description="翻页；首页留空，后续用上一页返回的 log_id",
    )
    sort_type: str = Field(
        default="0",
        description="排序：0=综合（默认），1=最多点赞，2=最新发布",
    )
    publish_time: str = Field(
        default="0",
        description="发布时间：0=不限，1=1天内，7=7天内，180=180天内",
    )
    filter_duration: str = Field(
        default="0",
        description="视频时长：0=不限，0-1=1分钟内，1-5=1-5分钟，1-10000=5分钟以上",
    )
    content_type: str = Field(
        default="0",
        description="内容形式：0=不限，1=视频，2=图文",
    )
    exclude_words: str = Field(default="", description="排除词，空格分隔")


class DouyinSearchAllBody(PublicSearchAllBody):
    keyword: str = Field(..., min_length=1)
    cursor: str = ""
    log_id: str = Field(default="", validation_alias=AliasChoices("log_id", "logid"))
    publish_time: str = ""
    filter_duration: str = ""
    content_type: str = ""


class XhsSearchPageBody(BaseModel):
    """小红书单页搜索（与第三方检索参数一致）。"""

    keyword: str = Field(..., min_length=1, description="搜索关键词")
    page: int = Field(default=1, ge=1, description="页码，默认 1")
    sort_type: str = Field(
        default="0",
        description="排序：0=综合（默认），1=最多点赞，2=最新发布",
    )
    content_type: str = Field(
        default="",
        description="笔记类型：video=视频笔记，note=普通笔记，空=不限",
    )
    note_time: str = Field(
        default="0",
        description="时间范围：0=不限，1=1天内，7=7天内，180=180天内",
    )
    exclude_words: str = Field(default="", description="排除词，空格分隔")


class XhsSearchAllBody(PublicSearchAllBody):
    keyword: str = Field(..., min_length=1)
    cursor: str = ""
    log_id: str = Field(default="", validation_alias=AliasChoices("log_id", "logid"))
    publish_time: str = ""
    filter_duration: str = ""
    content_type: str = ""
