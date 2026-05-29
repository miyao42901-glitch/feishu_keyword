# feishu/ 技术文档索引

## 适用范围

| 项 | 说明 |
|----|------|
| **对应代码目录** | 仓库根目录下的 **`feishu/`** |
| **职责** | 飞书生态内前端（插件页面、与多维表格等能力对接的 UI） |

---

## 技术栈

以 `feishu/package.json` 为准；当前主要依赖如下。

| 类别 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 | 组合式 API |
| 语言 | TypeScript | `vue-tsc` 参与构建校验 |
| 构建 | Vite 8 | `vite.config.ts` |
| UI | Element Plus | 组件库 |
| 样式 | Tailwind CSS 4 | `@tailwindcss/vite` |
| 状态 | Pinia | 全局状态 |
| 飞书 | `@lark-base-open/js-sdk` | 多维表格 / 开放能力 |
| 工具库 | dayjs | 时间处理 |

### 视图与页面私有组件

复杂页面使用 **`src/views/<功能名>/`** 目录：**`index.vue`** 为入口，`components/` 下放**仅本页使用**的子组件。约定见 **[DEVELOPMENT.md](../DEVELOPMENT.md)** 第二节。

当前示例：**新建任务** → `views/TaskCreateForm/index.vue` + `views/TaskCreateForm/components/`。

---

## 与本目录相关的规范文档

| 文档 | 说明 |
|------|------|
| [工程约定](../DEVELOPMENT.md) | 全仓库 Git、注释、环境安全 |
| [HTTP_API.md](../server/HTTP_API.md) | 后端 `/api/v1` 路径、Header、同步/异步任务 |
| [Nginx 反向代理](./NGINX.md) | 同源访问 `/api/v1`（8765）、`/yddm-api`（YDDM） |
| [组件命名与注释](./component-style.md) | `defineOptions` 组件名、注释约定 |

数据库表结构见 **[DATABASE.md](../DATABASE.md)**（后端 `server/` 维护）。

---

## 消费后端 API

业务请求发往同源 **`/api/v1/*`**（开发时由 Vite 代理到 `SYNC_PROXY_TARGET`，默认 `http://127.0.0.1:8765`）。

工程内封装：

- **`feishu/src/lib/async-task-api.ts`** — 异步任务 CRUD
- **`feishu/src/lib/*-sync-api.ts`** — 各平台同步搜索
- **`feishu/src/lib/sync-api-common.ts`** — 公共请求与错误处理

路径与 Header 约定见 **[HTTP_API.md](../server/HTTP_API.md)**。可复用逻辑放在 **`feishu/src/lib/*.ts`**；跨模块复用约定见 **[DEVELOPMENT.md](../DEVELOPMENT.md)** 第九节。

---

## 本地运行

环境变量在**仓库根**（`vite.config.ts` 的 `envDir` 指向仓根）：

```powershell
# 仓根
cp .env.test .env
cp .env.local.example .env.local   # 可选，改 SYNC_PROXY_TARGET 等

# 另开终端：后端（:8765）
cd server && python run.py

cd feishu
npm install
npm run dev          # 默认本机，Vite 代理 /api/v1 → 8765
npm run dev:lan      # 局域网联调
```

**不要**把 `VITE_*` 指到公网 API 域又在 `fskw-feishu.*` 打开页面（会跨域）；测试/正式静态由 **CI Runner** 编译（`build:public:test|prod`）。详见 **[NGINX.md](./NGINX.md)**。

构建与预览：

```powershell
npm run build
npm run preview
```
