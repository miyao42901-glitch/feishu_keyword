# 仓库协作说明（AI / 新成员）

本文件用于**新会话、新窗口**快速对齐：详细规则在 **`docs/`** 目录。

## 开始写代码之前

1. 阅读 **`docs/README.md`** 索引，再读与本次任务相关的 **`DEVELOPMENT.md` / `API.md` / `DATABASE.md`**。  
2. Cursor 已配置 **`.cursor/rules/dev-standards.mdc`**（`alwaysApply: true`），助手应自动结合上述文档行动。

## 项目入口

- 后端：`server/`，入口 `app.main:app`，API 前缀 `/api`。  
- 前端：`feishu/`，Vue 3 + Vite。

## 密钥

数据库等敏感配置仅放在 **`server/.env`**，勿提交、勿在聊天中发送真实密码。
