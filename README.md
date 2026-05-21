# 飞书关键词监控插件

## 当前项目

本项目是面向**飞书（Lark）**的**关键词监控插件**，用于在飞书生态内对关键词进行监控与相关能力扩展。

- **全称**：飞书关键词监控插件  
- **GitLab 仓库**：[http://192.168.1.200:8080/jzl/feishu_keyword/](http://192.168.1.200:8080/jzl/feishu_keyword/)

## 线上部署

主机目录：`/docker/feishu_keyword-test`（测试）、`/docker/feishu_keyword`（正式）。域名仍为 `fskw-*.tbpf.com`。

| 环境 | API | Admin | Feishu 静态 |
|------|-----|-------|-------------|
| 测试 | https://fskw-test.tbpf.com | https://fskw-admin-test.tbpf.com | https://fskw-feishu-test.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

探活：`GET https://fskw-test.tbpf.com/ci-test`

**测试管理后台登录**：https://fskw-admin-test.tbpf.com/login — 账号 `admin` / 密码 `Admin123a`（首次登录后请修改）

详细步骤见 [docs/DEPLOY.md](docs/DEPLOY.md)。

## 双后端

| 服务 | 路径前缀 | 目录 |
|------|----------|------|
| 业务 API（管理端、飞书任务配置） | `/api`、`/api/admin/v1`、`/ci-test` | `server/` |
| 采集/异步 API | `/api/v1` | `python/`（需 Celery Worker） |

## `public` 目录

| 路径 | 说明 |
|------|------|
| `public/admin/` | 管理端静态，本地 `build:public:*` 后提交主仓 |
| `public/feishu/` | 飞书静态，本地 `build:public:*` 后提交主仓 |

## 本地开发

```bash
cd server && cp .env.example .env
cd admin && npm run dev:local
cd feishu && npm run dev:local   # 采集 API 需另起 python/run.py :8765
```

部署前预编译（测试）：仓根 `build-public-test.bat`，提交 `public/admin`、`public/feishu` 后推送 `test` 分支。

## 目录结构

```
feishu_keyword/
├── docker-compose.yml      # 唯一编排真源（测试/正式靠栈目录 .env 区分）
├── build-public-test.bat
├── admin/
├── feishu/
├── python/                 # 采集与异步任务（lyc 分支合并）
├── server/
├── deploy/
├── public/
└── docs/
```
