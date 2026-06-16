"""同步接口 POST JSON 体：业务字段（与下游第三方 body 一致）；`X-API-Key` 仅通过 Header 传递。"""

from __future__ import annotations

from typing import Optional

from pydantic import AliasChoices, BaseModel, Field


class PublicSearchAllBody(BaseModel):
    """search-all 专用：多页采集控制字段（均未填时不写入 params）。"""

    exclude_words: Optional[str] = Field(default=None, description="排除词，空格分隔")
    fetch_count: Optional[int] = Field(
        default=None,
        ge=1,
        le=500,
        description="采集条数上限；达到或时间窗内无更多数据即停",
    )
    time_range: Optional[int] = Field(
        default=None,
        ge=1,
        description="时间范围（天）；仅 sort_type=2 时参与时间窗与第三方 days 映射",
    )
    sort_type: Optional[int] = Field(
        default=None,
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
    cursor: Optional[str] = Field(default=None, description="翻页游标")
    log_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("log_id", "logid"),
        description="翻页参数",
    )
    sort_type: Optional[str] = Field(
        default=None,
        description="排序：0=综合，1=最多点赞，2=最新发布",
    )
    publish_time: Optional[str] = Field(
        default=None,
        description="发布时间：0=不限，1=1天内，7=7天内，180=180天内",
    )
    filter_duration: Optional[str] = Field(
        default=None,
        description="视频时长：0=不限，0-1=1分钟内，1-5=1-5分钟，1-10000=5分钟以上",
    )
    content_type: Optional[str] = Field(
        default=None,
        description="内容形式：0=不限，1=视频，2=图文",
    )
    exclude_words: Optional[str] = Field(default=None, description="排除词，空格分隔")


class DouyinSearchAllBody(PublicSearchAllBody):
    keyword: str = Field(..., min_length=1)
    cursor: Optional[str] = None
    log_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("log_id", "logid"))
    publish_time: Optional[str] = None
    filter_duration: Optional[str] = None
    content_type: Optional[str] = None


class XhsSearchPageBody(BaseModel):
    """小红书单页搜索（与第三方检索参数一致）。"""

    keyword: str = Field(..., min_length=1, description="搜索关键词")
    page: Optional[int] = Field(default=None, ge=1, description="页码")
    sort_type: Optional[str] = Field(
        default=None,
        description="0=综合，1=最多点赞，2=最新，3=最多评论，4=最多收藏",
    )
    content_type: Optional[str] = Field(
        default=None,
        description="笔记类型：video=视频笔记，note=普通笔记，空=不限",
    )
    note_time: Optional[str] = Field(
        default=None,
        description="时间范围：0=不限，1=1天内，7=7天内，180=180天内",
    )
    exclude_words: Optional[str] = Field(default=None, description="排除词，空格分隔")


class XhsSearchAllBody(PublicSearchAllBody):
    keyword: str = Field(..., min_length=1)
    sort_type: Optional[str] = Field(
        default=None,
        description="0=综合，1=最多点赞，2=最新，3=最多评论，4=最多收藏",
    )
    cursor: Optional[str] = None
    log_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("log_id", "logid"))
    publish_time: Optional[str] = None
    filter_duration: Optional[str] = None
    content_type: Optional[str] = None
    note_time: Optional[str] = Field(
        default=None,
        description="时间范围：0=不限，1=1天内，7=7天内，180=180天内",
    )


class WxSosoSearchPageBody(BaseModel):
    """视频号 /wx/sousou 单页搜索。"""

    keyword: str = Field(..., min_length=1, description="搜索关键词")
    mode: Optional[int] = Field(default=None, description="模式")
    search_type: Optional[int] = Field(default=None, description="搜索类型")
    note_time: Optional[int] = Field(default=None, description="0不限 1最近1天 2最近7天 3最近半年")
    sort_type: Optional[int] = Field(default=None, description="0综合 1最新 2最热")
    page: Optional[int] = Field(default=None, ge=1, description="页码（与 currentPage 等效）")
    currentPage: Optional[int] = Field(default=None, ge=1, description="页码")
    offset: Optional[int] = Field(default=None, description="翻页 offset")
    cookies_buffer: Optional[str] = Field(default=None, description="翻页 cookies")
    content_type: Optional[str] = Field(default=None, description="内容类型")
    exclude_words: Optional[str] = Field(default=None, description="排除词")


class WxSosoSearchAllBody(PublicSearchAllBody):
    """视频号多页搜索。"""

    keyword: str = Field(..., min_length=1)
    mode: Optional[int] = None
    search_type: Optional[int] = None
    note_time: Optional[int] = Field(default=None, description="0不限 1最近1天 2最近7天 3最近半年")
    sort_type: Optional[int] = None
    page: Optional[int] = Field(default=None, ge=1)
    currentPage: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = None
    cookies_buffer: Optional[str] = None
    content_type: Optional[str] = None


class MpSearchPageBody(BaseModel):
    """公众号单页搜索（复用视频号逻辑，mode=2, BusinessType=2）。"""

    keyword: str = Field(..., min_length=1, description="搜索关键词")
    sort_type: Optional[int] = Field(default=None, description="0->Sub_search_type=0, 1->4, 2->2")
    note_time: Optional[int] = Field(default=None, description="时间范围")
    page: Optional[int] = Field(default=None, ge=1, description="页码（内部映射为 currentPage）")
    currentPage: Optional[int] = Field(default=None, ge=1, description="页码")
    offset: Optional[int] = Field(default=None, description="翻页 offset")
    cookies_buffer: Optional[str] = Field(default=None, description="翻页 cookies")
    exclude_words: Optional[str] = Field(default=None, description="排除词")


class MpSearchAllBody(PublicSearchAllBody):
    """公众号多页搜索。"""

    keyword: str = Field(..., min_length=1)
    sort_type: Optional[int] = None
    note_time: Optional[int] = None
    page: Optional[int] = Field(default=None, ge=1)
    currentPage: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = None
    cookies_buffer: Optional[str] = None
