from social_platform.models.results.douyin_search_result import DouyinSearchResult
from social_platform.models.results.registry import (
    get_result_model,
    list_supported_platforms,
    natural_key_field,
    result_table_factory,
)
from social_platform.models.results.xhs_search_result import XhsSearchResult

__all__ = [
    "DouyinSearchResult",
    "XhsSearchResult",
    "get_result_model",
    "result_table_factory",
    "list_supported_platforms",
    "natural_key_field",
]
