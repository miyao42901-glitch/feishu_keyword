# 仓库协作说明（AI / 新成员）

本文件用于**新会话、新窗口**快速对齐：详细规则在 **`docs/`** 目录。

## 开始写代码之前

1. 阅读 **`docs/README.md`** 与 **`docs/GIT_WORKFLOW.md`**（分支与部署）；按任务选择 **`docs/server/README.md`**（改后端）或 **`docs/feishu/README.md`**（改前端），再读 **`DEVELOPMENT.md`** 及相关的 **`API.md` / `DATABASE.md`**。联调 HTTP 时须遵守 **`docs/API.md`** 中 **统一响应 `code` / `message` / `data`**（第五节）。  
2. 若存在 **`.cursor/rules/dev-standards.mdc`**（`alwaysApply: true`），助手应结合上述文档行动。

## 项目入口

- 后端：`server/` → 技术栈与索引见 **`docs/server/README.md`**，入口 `app.main:app`，API 前缀 `/api`。  
- 前端：`feishu/` → 技术栈与索引见 **`docs/feishu/README.md`**。

## 密钥

数据库等敏感配置仅放在**仓库根**（`.env.test` / `.env.master` 复制为 `.env`；本地可用 `.env.local`），勿提交、勿在聊天中发送真实密码。

## 部署（摘要）

- 个人分支开发 → **本地 merge 到 `test`** → `git push origin test` → 自动部署测试栈；**GitLab MR 合并 `master`** → 流水线手动 **`deploy-prod`**。
- 发布前可选本地 `build-public-test.bat` / `build-public-prod.bat` 预检；CI 在 Runner 自动编译。详见 **`docs/GIT_WORKFLOW.md`**、**`docs/DEPLOY.md`**。
