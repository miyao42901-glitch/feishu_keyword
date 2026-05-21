# 飞书关键词监控插件

## 当前项目

本项目是面向**飞书（Lark）**的**关键词监控插件**，用于在飞书生态内对关键词进行监控与相关能力扩展。

- **全称**：飞书关键词监控插件  
- **GitLab 仓库**：[http://192.168.1.200:8080/jzl/feishu_keyword/](http://192.168.1.200:8080/jzl/feishu_keyword/)

## 线上部署（fskw）

| 环境 | API | Admin | Feishu 静态 |
|------|-----|-------|-------------|
| 测试 | https://fskw-test.tbpf.com | https://fskw-admin-test.tbpf.com | https://fskw-feishu-test.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

探活：`GET /ci-test`（如 `https://fskw-test.tbpf.com/ci-test`）。

详细步骤见 [docs/DEPLOY.md](docs/DEPLOY.md)。

## `public` 目录

| 路径 | 说明 |
|------|------|
| `public/admin/` | 管理端静态，**提交主仓** |
| `public/feishu/` | 飞书构建产物 + **GitHub 手动发布**（主仓忽略） |

## 本地开发

```bash
cd server && cp .env.example .env
cd admin && npm run dev:local
cd feishu && npm run dev:local
```

## 目录结构

```
feishu_keyword/
├── docker-compose.yml
├── docker-compose.test.yml
├── docker-compose.prod.yml
├── .gitlab-ci.yml
├── release.bat
├── admin/
├── feishu/
├── server/
├── deploy/
├── public/admin/
└── docs/
```
