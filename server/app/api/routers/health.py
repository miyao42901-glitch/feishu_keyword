"""
健康检查与运行状态接口。

响应统一为 `{ code, message, data }`，成功时 `code=0`。
"""

from fastapi import APIRouter

from app.db import check_database
from app.schemas.api_response import ApiResponse

router = APIRouter()


@router.get("/health")
def health() -> ApiResponse[dict]:
    """
    服务存活探测，并附带数据库配置与连通状态。

    路径：`GET /api/health`。

    Returns:
        统一信封 `ApiResponse`：`code=0` 时 `data` 为字典，含：
        - `status`：固定 `"ok"` 表示进程可用；
        - `service`：服务名 `"feishu_keyword"`；
        - `database`：`configured` 是否配置了 `DATABASE_URL`；若已配置则含 `reachable`、失败时可选 `error` 文案。

    Note:
        外层仍为 `{ code, message, data }`，见 `docs/API.md` 第五节。
    """
    out: dict = {"status": "ok", "service": "feishu_keyword"}
    ok, err = check_database()
    if err == "not_configured":
        out["database"] = {"configured": False}
    else:
        out["database"] = {
            "configured": True,
            "reachable": ok,
            **({"error": err} if err else {}),
        }
    return ApiResponse.success(data=out, message="服务正常")
