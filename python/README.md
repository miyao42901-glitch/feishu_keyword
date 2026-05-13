# Python 层架构说明

本目录承载**爬虫 Worker** 及其配套工具。业务流程代码在仓库根目录的 **`server/`** 与 **`feishu/`**；与 **`python/workers/`**、**`python/social_platform/`** 在代码上**禁止互相 import** 到业务包、无与 `server` 共享的 Python 包。

**解释器版本**：本目录下代码与依赖按 **Python 3.9.x** 编写与测试（见 `pyproject.toml` 的 `requires-python`）；请勿使用 3.10 及以上运行，以免类型与三方库行为不一致。

## 统一 HTTP（推荐）

- 在 `python/` 下安装依赖：`pip install -r requirements-http.txt`
- 启动：**`python run.py`**（默认 `0.0.0.0:8765`，可用环境变量 `HTTP_HOST`、`HTTP_PORT`、`HTTP_RELOAD`）
- 路由：统一前缀 **`/api/v1`** — `GET /api/v1/health`；抖音/小红书 **`POST /api/v1/sync/...`**（**Query：`key`** + **扁平 JSON Body**）；聚合 **`POST /api/v1/run`**（见 `HTTP_API.md`）
- **接口说明（路径、参数、响应格式）**：见 **`HTTP_API.md`**

## 目录一览

| 路径 | 作用 |
|------|------|
| `run.py` + `http_service.py` | **统一 FastAPI**，单端口对外 |
| `http_api/` | 对外 API 版本：`v1/` 等；常量见 `http_api/versions.py` |
| `HTTP_API.md` | **HTTP 数据接口**说明（`X-API-KEY`、`POST /api/v1/run`） |
| `requirements-http.txt` | 运行 `run.py` 所需依赖 |
| `workers/` | 仅 **`douyin_worker/`**、**`xhs_worker/`** |
| `social_platform/` | 共享 HTTP / 聚合任务 / 响应与 Schema（供上述 Worker 引用） |
| `extra/` | 非运行时占位或历史残留（如原 `multi_social` 的依赖清单） |
| `contracts/` | 请求/响应 JSON 的文档与 Schema，**非运行时共享库** |
| `.env` | 本地密钥与 URL；勿提交。可复制 **`python/.env.example`** |

## 设计原则

1. **隔离**：`server` / `feishu` 与 `python/workers/*` 无 Python 依赖关系。
2. **Worker 自治**：各 Worker 自带依赖文件与 Python 版本策略。
3. **契约**：路径与 JSON 形状见各 Worker `README.md` 与 `contracts/`。
