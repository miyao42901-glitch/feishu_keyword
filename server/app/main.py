"""
飞书关键词监控插件 —— FastAPI 应用入口。

职责：
- 创建 `FastAPI` 实例；
- 挂载统一前缀 `/api` 下的业务路由（见 `app.api.router`）。
"""

from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(title="feishu_keyword", version="0.1.0")
app.include_router(api_router, prefix="/api")
