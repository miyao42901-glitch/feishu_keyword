"""Deprecated: use ``social_platform.utils.worker_runtime``."""
from social_platform.utils.worker_runtime import (
    API_KEY_HEADER,
    resolved_service_url,
    split_exclude_needles,
    text_contains_any_needle,
    worker_meta,
)

__all__ = [
    "API_KEY_HEADER",
    "resolved_service_url",
    "split_exclude_needles",
    "text_contains_any_needle",
    "worker_meta",
]
