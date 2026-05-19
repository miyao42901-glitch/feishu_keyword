"""
异步任务 Action 注册表：唯一合法入口，禁止在路由里堆 if/else 分发。

- 对外 `action` 使用 kebab-case（如 `douyin-search-all`）。
- `platform` 仅来自注册项，不写数据库；执行 Worker 时使用 `worker_action`（snake_case）。
"""

from __future__ import annotations

import sys
from pathlib import Path

# Celery 等工作目录可能不是仓库 ``python/``，须保证其根在 ``sys.path`` 上，才能 ``import http_sync_bodies``。
_repo_py = Path(__file__).resolve().parent.parent.parent
for _d in (_repo_py, _repo_py / "workers"):
    _s = str(_d.resolve())
    if _s not in {str(Path(p).resolve()) for p in sys.path if isinstance(p, str) and p}:
        sys.path.insert(0, _s)

from dataclasses import dataclass
from typing import Any, Callable, Optional, Type

from pydantic import BaseModel

from http_sync_bodies import (
    DouyinSearchAllBody,
    DouyinSearchPageBody,
    MpSearchAllBody,
    MpSearchPageBody,
    WxSosoSearchAllBody,
    WxSosoSearchPageBody,
    XhsSearchAllBody,
    XhsSearchPageBody,
)
from social_platform.schemas.async_action_bodies import (
    DouyinSearchDetailBody,
    XhsSearchDetailBody,
)
from social_platform.utils.param_dict import prune_empty_string_fields, to_worker_params


@dataclass(frozen=True)
class ActionSpec:
    """单个对外 action 的元数据与校验模型。"""

    platform: str
    body_model: Type[BaseModel]
    worker_action: Optional[str]
    """为 None 且存在 `stub_runner` 时走占位逻辑。"""
    persist_crawl: bool
    """是否在爬取成功后写入 feishu_*_results。"""
    stub_runner: Optional[Callable[[dict[str, Any]], dict[str, Any]]] = None


def _detail_stub(platform: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def _run(_payload: dict[str, Any]) -> dict[str, Any]:
        from social_platform.utils.worker_runtime import worker_meta

        return {
            "ok": False,
            "error": f"{platform} search-detail is not implemented",
            "meta": worker_meta("async_task", "1.0.0"),
        }

    return _run


ACTION_REGISTRY: dict[str, ActionSpec] = {
    "douyin-search-all": ActionSpec(
        platform="douyin",
        body_model=DouyinSearchAllBody,
        worker_action="douyin_search_all",
        persist_crawl=True,
    ),
    "douyin-search-page": ActionSpec(
        platform="douyin",
        body_model=DouyinSearchPageBody,
        worker_action="douyin_search_page",
        persist_crawl=True,
    ),
    "douyin-search-detail": ActionSpec(
        platform="douyin",
        body_model=DouyinSearchDetailBody,
        worker_action=None,
        persist_crawl=False,
        stub_runner=_detail_stub("douyin"),
    ),
    "xhs-search-all": ActionSpec(
        platform="xhs",
        body_model=XhsSearchAllBody,
        worker_action="xhs_search_all",
        persist_crawl=True,
    ),
    "xhs-search-page": ActionSpec(
        platform="xhs",
        body_model=XhsSearchPageBody,
        worker_action="xhs_search_page",
        persist_crawl=True,
    ),
    "xhs-search-detail": ActionSpec(
        platform="xhs",
        body_model=XhsSearchDetailBody,
        worker_action=None,
        persist_crawl=False,
        stub_runner=_detail_stub("xhs"),
    ),
    "wxvideo-search-page": ActionSpec(
        platform="wxvideo",
        body_model=WxSosoSearchPageBody,
        worker_action="wx_sousou_search_page",
        persist_crawl=True,
    ),
    "wxvideo-search-all": ActionSpec(
        platform="wxvideo",
        body_model=WxSosoSearchAllBody,
        worker_action="wx_sousou_search_all",
        persist_crawl=True,
    ),
    "mp-search-page": ActionSpec(
        platform="mp",
        body_model=MpSearchPageBody,
        worker_action="mp_search_page",
        persist_crawl=True,
    ),
    "mp-search-all": ActionSpec(
        platform="mp",
        body_model=MpSearchAllBody,
        worker_action="mp_search_all",
        persist_crawl=True,
    ),
}


def list_registered_actions() -> tuple[str, ...]:
    return tuple(sorted(ACTION_REGISTRY.keys()))


def get_action_spec(action: str) -> Optional[ActionSpec]:
    key = (action or "").strip()
    if not key:
        return None
    return ACTION_REGISTRY.get(key)


def require_action_spec(action: str) -> ActionSpec:
    spec = get_action_spec(action)
    if spec is None:
        raise LookupError(action)
    return spec


def validate_body_for_action(action: str, body: Any) -> BaseModel:
    spec = require_action_spec(action)
    if not isinstance(body, dict):
        body = {}
    return spec.body_model.model_validate(body)


def body_dict_for_db(validated: BaseModel) -> dict[str, Any]:
    """入库 `body_json`：与 Worker 入参一致（不含 key），扁平/别名规范化，并去掉值为 `""` 的字段。"""
    raw = to_worker_params(validated.model_dump(mode="python"))
    return prune_empty_string_fields(raw)


def platform_for_persist(public_action: str) -> Optional[str]:
    """落库解析用平台标识；非爬取类 action 返回 None。"""
    spec = get_action_spec(public_action)
    if spec is None:
        return _legacy_platform_from_snake_action(public_action)
    if not spec.persist_crawl:
        return None
    return spec.platform


def _legacy_platform_from_snake_action(action: str) -> Optional[str]:
    a = (action or "").strip()
    if a.startswith("douyin_"):
        return "douyin"
    if a.startswith("xhs_"):
        return "xhs"
    if a.startswith("wx_sousou_") or a.startswith("wxvideo_"):
        return "wxvideo"
    if a.startswith("mp_") or a.startswith("mp-search"):
        return "mp"
    return None


def platform_for_result_listing(public_action: str) -> Optional[str]:
    """结果分页：任意已注册 action 返回其 platform；旧 action 用前缀推断。"""
    spec = get_action_spec(public_action)
    if spec is not None:
        return spec.platform
    return _legacy_platform_from_snake_action(public_action)
