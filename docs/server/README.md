# server/ 技术文档索引

## 适用范围

| 项 | 说明 |
|----|------|
| **对应代码目录** | 仓库根目录下的 **`server/`** |
| **职责** | HTTP API、MySQL 访问、业务服务；与飞书开放平台交互时可在本目录扩展客户端封装 |

---

## 技术栈

以 `server/requirements.txt` 为准；当前约定如下。

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3 | 建议使用 3.10+（与本地虚拟环境一致） |
| Web 框架 | FastAPI | 路由、依赖注入、OpenAPI |
| ASGI 服务器 | Uvicorn | 开发：`uvicorn app.main:app` |
| ORM | SQLAlchemy 2.x | 模型见 `app/models/` |
| 数据库驱动 | PyMySQL | 经连接串 `mysql+pymysql://...` |
| 配置 | python-dotenv | 从 `server/.env` 加载 `DATABASE_URL` |
| HTTP 客户端 | httpx | 调用外部 API（飞书、采集服务等） |

---

## 与本目录相关的规范文档

| 文档 | 说明 |
|------|------|
| [HTTP 接口规范](../API.md) | `/api` 前缀、REST 命名、分页、响应约定 |
| [数据库与 ORM](../DATABASE.md) | 库名、表字段、`DATABASE_URL`、变更清单 |
| [工程约定](../DEVELOPMENT.md) | 分层目录、`get_db`、Git 与注释 |

---

## 本地运行

```powershell
cd server
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- 健康检查：`GET http://127.0.0.1:8000/api/health`
- OpenAPI：`http://127.0.0.1:8000/docs`

---

## 代码分层（摘要）

详见 [DEVELOPMENT.md](../DEVELOPMENT.md) 第二节：`app/main.py` → `api/router.py` → `api/routers/` → `services/` → `models/` / `schemas/`。
