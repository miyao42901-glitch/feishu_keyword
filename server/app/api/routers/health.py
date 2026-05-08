"""
健康检查与运行状态接口。
"""

from fastapi import APIRouter

from app.db import check_database

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """
    服务存活探测，并附带数据库配置与连通状态。

    Returns:
        包含 `status`、`service` 以及 `database` 子对象（configured / reachable / error）的字典。
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
    return out
