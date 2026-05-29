"""限流 scope：每个 HTTP 路由独立桶，禁止多接口共用同一 scope（如 async_list）。"""

from __future__ import annotations

# --- 异步任务 /api/v1/async/... ---
ASYNC_SUBMIT = "async_submit"
ASYNC_TASK_EDIT = "async_task_edit"
ASYNC_TASK_LIST = "async_task_list"
ASYNC_TASK_STATUS = "async_task_status"
ASYNC_TASK_RESULTS = "async_task_results"
ASYNC_TASK_CANCEL = "async_task_cancel"
ASYNC_TASK_DELETE = "async_task_delete"
ASYNC_TASK_RESTART = "async_task_restart"

# --- 结果验收 /api/v1/results/... ---
RESULT_ACCEPTANCE_PENDING = "result_acceptance_pending"
RESULT_ACCEPTANCE_ACCEPT = "result_acceptance_accept"

# --- 同步 /api/v1/sync/...（按平台+模式拆分）---
SYNC_RUN = "sync_run"
SYNC_SEARCH_PAGE = "sync_search_page"
SYNC_SEARCH_ALL = "sync_search_all"
