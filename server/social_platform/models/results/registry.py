"""按 platform 解析到具体结果 ORM（扩展新平台时在此注册）。"""

from __future__ import annotations

from typing import Type

from social_platform.models.base import Base
from social_platform.models.results.douyin_search_result import DouyinSearchResult
from social_platform.models.results.mp_search_result import MpSearchResult
from social_platform.models.results.wxvideo_search_result import WxVideoSearchResult
from social_platform.models.results.xhs_search_result import XhsSearchResult

_RESULT_MODELS: dict[str, Type[Base]] = {
    "douyin": DouyinSearchResult,
    "xhs": XhsSearchResult,
    "wxvideo": WxVideoSearchResult,
    "mp": MpSearchResult,
}


def list_supported_platforms() -> tuple[str, ...]:
    return tuple(sorted(_RESULT_MODELS.keys()))


def get_result_model(platform: str) -> Type[Base]:
    key = (platform or "").strip().lower()
    model = _RESULT_MODELS.get(key)
    if model is None:
        raise ValueError(
            f"unsupported result platform: {platform!r}; supported={list_supported_platforms()}"
        )
    return model


def result_table_factory(platform: str) -> Type[Base]:
    """按 platform 取对应结果表 ORM（与 `get_result_model` 同义，命名强调「结果表」）。"""
    return get_result_model(platform)


def natural_key_field(platform: str) -> str:
    """业务主键列名（统一为 post_id）。"""
    key = (platform or "").strip().lower()
    if key in _RESULT_MODELS:
        return "post_id"
    raise ValueError(f"unsupported platform: {platform!r}")
