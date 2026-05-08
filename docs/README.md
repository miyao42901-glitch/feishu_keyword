# 项目文档索引

本目录存放**开发规则、接口与数据约定**等说明，供人工与 AI 助手在改代码前对齐标准。

| 文档 | 内容 |
|------|------|
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 仓库结构、分层职责、注释与提交、环境与安全 |
| [API.md](./API.md) | REST 路径、HTTP 语义、请求/响应与分页约定 |
| [DATABASE.md](./DATABASE.md) | 库名、`DATABASE_URL`、全表字段说明、ORM 与变更清单 |

**新开会话或接手开发时**：先读 `DEVELOPMENT.md` 与本次任务相关的另一篇；根目录 [`AGENTS.md`](../AGENTS.md) 与 [`.cursor/rules/`](../.cursor/rules/) 会要求助手优先查阅此处。
