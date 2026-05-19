"""由已注册 `action` + `body_json` + API Key 执行聚合 Worker 或占位逻辑。"""

from __future__ import annotations

from typing import Any

from social_platform.actions.registry import get_action_spec


def execute_public_action(
    public_action: str, body_json: dict[str, Any], api_key: str
) -> dict[str, Any]:
    """
    :param public_action: 对外 kebab-case（新）或历史 snake_case（如 `douyin_search_all`）
    :param body_json: 任务表 `body_json` 中的字典（不含 key）
    :param api_key: 来自异步提交时的 Header，仅存在于 Celery 消息中
    """
    spec = get_action_spec(public_action)
    params = dict(body_json or {})
    params["key"] = (api_key or "").strip()

    if spec is not None:
        if spec.stub_runner is not None:
            return spec.stub_runner({"action": public_action, "params": params})

        from social_platform.aggregated_job import run_task as run_aggregated

        wa = spec.worker_action
        if not wa:
            raise RuntimeError(f"invalid registry entry for action {public_action!r}")
        return run_aggregated({"action": wa, "params": params})

    # 历史任务：库中仍为 `douyin_*` / `xhs_*` action
    a = (public_action or "").strip()
    if a.startswith("douyin_") or a.startswith("xhs_"):
        from social_platform.aggregated_job import run_task as run_aggregated

        return run_aggregated({"action": a, "params": params})

    raise LookupError(public_action)
