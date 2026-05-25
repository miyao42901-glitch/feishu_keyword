"""
关键词监控 —— FastAPI 应用入口。

职责：
- 创建 `FastAPI` 实例；
- 挂载统一前缀 `/api` 下的业务路由（见 `app.api.router`）。
"""

import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.exception_handlers import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from admin.router import admin_router
from app.api.router import api_router
from app.ci_build_info import read_build_info
from app.health_probes import mysql_ok, redis_ok

app = FastAPI(title="feishu_keyword", version="0.1.0")

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 浏览器从局域网 IP（如 http://192.168.x.x:5173）访问时，与 http://127.0.0.1:8000 为跨域。
# 使用正则按请求的 Origin 回显，避免部分环境下仅 allow_origins=["*"] 仍缺头的问题。
# 生产环境请改为明确域名白名单或环境变量配置。
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://[^\s]+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(admin_router, prefix="/api/admin/v1")


@app.get("/ci-test")
def ci_test():
    info = read_build_info()
    env_name = os.getenv("ENVIRONMENT", "local")
    return {
        "source": f"feishu_keyword-{env_name}",
        "ci": bool(info),
        "build": info.get("build", "local-dev"),
        "commit": info.get("commit", "unknown"),
        "branch": info.get("branch", "unknown"),
        "deployed_at": info.get("deployed_at", "unknown"),
        "mysql_ok": mysql_ok(),
        "redis_ok": redis_ok(),
    }
