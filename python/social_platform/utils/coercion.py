from __future__ import annotations

from typing import Any


def as_third_party_str(v: Any) -> str:
    """None → 空串，其余 `str(v)`。"""
    if v is None:
        return ""
    return str(v)
