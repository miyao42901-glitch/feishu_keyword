"""对外 Pydantic：聚合信封 + 异步任务 API 模型。"""

from social_platform.schemas.async_submit import AsyncTaskSubmitRequest
from social_platform.schemas.async_task import (
    AsyncTaskResultsResponse,
    AsyncTaskStatusResponse,
    AsyncTaskSubmitResponse,
)
from social_platform.schemas.task_envelope import TaskEnvelope

__all__ = [
    "TaskEnvelope",
    "AsyncTaskSubmitRequest",
    "AsyncTaskSubmitResponse",
    "AsyncTaskStatusResponse",
    "AsyncTaskResultsResponse",
]
