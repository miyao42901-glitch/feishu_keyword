"""对外统一业务状态码（与 HTTP 响应体字段 `code` 一致）。"""

from __future__ import annotations

# --- 标准码（文档与客户端约定）---

CODE_FAILED = -1  # 失败
CODE_SUCCESS = 0  # 成功
CODE_BAD_REQUEST = 400  # 参数错误
CODE_INSUFFICIENT_BALANCE = 1001  # 余额不足
CODE_INVALID_API_KEY = 1005  # 无效的 API Key（与 API_STATUS_MESSAGES 一致）
CODE_USER_NOT_FOUND = 1006  # 用户不存在
CODE_REQUEST_LIMIT_EXCEEDED = 1003  # 请求频率超过上限（历史 yddm 码）
CODE_ASYNC_SUBMIT_USER_MISMATCH = 1020  # X-User-Id 与 X-API-Key 在 yddm 侧不一致
CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED = 1021  # 单用户 pending/running 异步任务数超限
CODE_ASYNC_SUBMIT_DUPLICATE = 1026  # 相同用户、相同参数的任务已存在（进行中）
CODE_ASYNC_TASK_ALREADY_CANCELLED = 1027  # 异步任务已取消，重复取消
CODE_ASYNC_TASK_ALREADY_ACTIVE = 1028  # 任务进行中，无法重启
CODE_ASYNC_TASK_WINDOW_ENDED = 1029  # 定时窗口已结束，无法重启
CODE_YDDM_USERS_ME_FAILED = 1022  # 调用 yddm「当前用户」接口失败或不可用
CODE_NOT_FOUND = 1023  # 资源不存在（如异步任务 id）
CODE_SERVICE_UNAVAILABLE = 1024  # 服务未配置或暂不可用（如未设置 DATABASE_URL）
CODE_RATE_LIMIT_EXCEEDED = 1025  # 请求频率超过上限（如 IP 限流）
CODE_UNSUPPORTED_ACTION = 1019  # 不支持的 action

# Spider / HTTP 层内部使用的临时码，对外映射为 api_status_codes 中已有码
_INTERNAL_HTTP_ERROR = 5001
_INTERNAL_PARSE_OR_RETRY = 5000
_INTERNAL_RETRY_EXHAUSTED = 5002

API_STATUS_MESSAGES: dict[int, str] = {
    -1: "failed",
    0: "success",
    400: "参数错误",
    1001: "账户余额不足",
    1002: "邮箱/手机号或密码错误",
    1003: "请求频率超过上限",
    1004: "邮箱或手机号已注册",
    1005: "无效的 API Key",
    1006: "用户不存在",
    1007: "登录凭证无效",
    1008: "缺少 API Key",
    1009: "手机或邮箱已存在",
    1010: "需要管理员授权",
    1011: "原密码错误",
    1012: "新密码不能与原密码相同",
    1013: "手机号和uid不能都为空",
    1014: "请填写验证码",
    1015: "验证码错误或已过期",
    1016: "登录失败次数过多，请输入验证码",
    1017: "请填写手机号",
    1018: "请填写邮箱",
    1019: "接口不存在，请检查",
    1020: "X-User-Id 与当前 API Key 对应的用户不一致",
    1021: "异步任务数量已达上限，请等待进行中的任务完成后再提交",
    1026: "已存在相同参数的进行中任务，请勿重复提交",
    1027: "任务已取消，无需重复操作",
    1028: "任务进行中，无法重启",
    1029: "定时窗口已结束，无法重启",
    1022: "用户校验服务暂时不可用，请稍后重试",
    1023: "资源不存在",
    1024: "服务暂不可用，请稍后重试",
    1025: "请求频率超过上限，请稍后重试",
    5000: "服务暂时不可用，请稍后重试",
    5003: "网络连接失败，请稍后重试",
    6001: "修改密码失败，请稍后重试",
}


def get_message(code: int) -> str:
    """返回状态码对应说明；未知码回退为 failed。"""
    return API_STATUS_MESSAGES.get(int(code), API_STATUS_MESSAGES[CODE_FAILED])


def normalize_upstream_error_code(code: int) -> int:
    """
    将爬虫/HTTP 层内部错误码映射为对外标准码。
    大加拉等业务码（如 1005）不在此列，原样返回。
    """
    c = int(code)
    if c == _INTERNAL_HTTP_ERROR:
        return 5003
    if c in (_INTERNAL_PARSE_OR_RETRY, _INTERNAL_RETRY_EXHAUSTED):
        return 5000
    return c
