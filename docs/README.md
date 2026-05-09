# 项目文档索引

本目录存放**开发规则、接口与数据约定**等说明；**按仓库子目录**查阅时，优先看对应子文档中的「适用范围」与 **`docs/server/`**、**`docs/feishu/`** 索引。

## 按代码目录查找

| 代码目录 | 文档入口 | 技术栈说明 |
|----------|----------|------------|
| **`server/`** | [server/README.md](./server/README.md) | 后端技术栈、运行方式、规范链接 |
| **`feishu/`** | [feishu/README.md](./feishu/README.md) | 前端技术栈、运行方式、与后端协作 |
| **全仓库** | [DEVELOPMENT.md](./DEVELOPMENT.md) | 目录结构、分层、Git、环境 |

## 专项规范（均含「适用范围」前置说明）

| 文档 | 内容 | 主要对应目录 |
|------|------|----------------|
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 仓库结构、分层职责、注释与提交、环境与安全 | 全仓库 |
| [API.md](./API.md) | REST 路径、HTTP 语义、分页、**统一响应 `code` / `message` / `data`** | `server/`；前端联调时必读第五节 |
| [DATABASE.md](./DATABASE.md) | 库名、`DATABASE_URL`、全表字段说明、ORM 与变更清单 | `server/` |

**新开会话或接手开发时**：先根据要改的目录打开 **server** 或 **feishu** 索引，再读 [DEVELOPMENT.md](./DEVELOPMENT.md) 与相关专项文档；根目录 [`AGENTS.md`](../AGENTS.md) 为协作总入口。
