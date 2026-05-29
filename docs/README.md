# 文档索引

## 部署与 CI（GitLab）

| 分支 | 触发 | 任务 | 目标栈 |
|------|------|------|--------|
| **`test`** | 推送后**自动** | `deploy-test` | `/docker/feishu_keyword-test` |
| **`master`** | **MR 合并**后产生流水线，**手动**运行 | `deploy-prod` | `/docker/feishu_keyword` |

推荐流程：个人分支（如 `hxp`）→ **本地 merge 到 `test`** → `git push origin test` → 验收 → `build-public-prod.bat` → GitLab **MR** `test`→`master` → 手动 `deploy-prod`。详见 **[GIT_WORKFLOW.md](./GIT_WORKFLOW.md)**。

Runner **不安装 Node**；须在本地构建 `public/admin`、`public/feishu` 后提交，CI 仅 rsync。详见 **[DEPLOY.md](./DEPLOY.md)**。

**编排真源**：仓库根 [`docker-compose.yml`](../docker-compose.yml)、[`.gitlab-ci.yml`](../.gitlab-ci.yml)（仅此一份 compose，测试/正式靠主机目录与栈根 `.env` 区分）。

---

## 环境变量（仓根统一）

| 文件 | 用途 |
|------|------|
| `.env.example` | 字段说明与模板索引 |
| `.env.test` / `.env.master` | 测试 / 正式**源文件**（可提交占位版） |
| `.env` | 生效文件（gitignore）；部署时 `cp -f .env.test` 或 `.env.master` 覆盖 |
| `.env.local.example` → `.env.local` | 本机 / 局域网联调覆盖（gitignore） |

`server/`、`python/`、`admin/`、`feishu/` 的 Vite **均从仓根**加载 `.env` → `.env.local`。勿再维护 `server/.env*`、`python/.env*`、`*/.env.local.example` 等子目录 env 模板。

---

## 文档列表

| 文档 | 说明 |
|------|------|
| [GIT_WORKFLOW.md](./GIT_WORKFLOW.md) | **Git 分支与部署协作规范**（个人分支、test 合并、MR 发正式） |
| [DEPLOY.md](./DEPLOY.md) | 主机目录、域名、Docker、CI、验收 curl |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 全仓库工程约定、构建、分层 |
| [DATABASE.md](./DATABASE.md) | 库表、`DATABASE_URL` |
| [API.md](./API.md) | HTTP 接口与统一响应体 |
| [server/README.md](./server/README.md) | `server/` 技术栈与分层 |
| [feishu/README.md](./feishu/README.md) | `feishu/` 技术栈与本地运行 |
| [feishu/NGINX.md](./feishu/NGINX.md) | 同源反代、`VITE_*` 与生产静态 |
| [feishu/component-style.md](./feishu/component-style.md) | 组件命名与注释 |
| [../admin/README.md](../admin/README.md) | 管理端 `admin/` |
| [../python/DEPLOYMENT.md](../python/DEPLOYMENT.md) | 采集 HTTP + Celery 部署 |
| [../python/migrations/README.md](../python/migrations/README.md) | 采集库 `schema.sql` 与增量 SQL（001–011） |
| [../AGENTS.md](../AGENTS.md) | AI / 新成员入口 |
