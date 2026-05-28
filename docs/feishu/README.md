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
| 飞书 | `@lark-base-open/js-sdk` | 多维表格 / 开放能力（版本以 package.json 为准） |
| 工具库 | dayjs | 时间处理 |
| 工程插件 | unplugin-auto-import、unplugin-vue-components | 自动导入 |

### 视图与页面私有组件

复杂页面使用 **`src/views/<功能名>/`** 目录：**`index.vue`** 为入口，`components/` 下放**仅本页使用**的子组件；类型与选项列表可放同级 `types.ts`、`constants.ts`。约定见 **[DEVELOPMENT.md](../DEVELOPMENT.md)** 第二节「前端复杂页面与私有组件」。

当前示例：**新建任务** → `views/TaskCreateForm/index.vue` + `views/TaskCreateForm/components/`。

---

## 与本目录相关的规范文档

| 文档 | 说明 |
|------|------|
| [工程约定](../DEVELOPMENT.md) | 全仓库 Git、注释、环境安全 |
| [HTTP 接口规范](../API.md) | 若前端直连 **`server/`**：路径、分页、**统一响应 `code` / `message` / `data`**（第五节）；飞书任务接口见同文档 §8 |
| [Nginx 反向代理](./NGINX.md) | 同源访问 `/api/v1`（8765）、`/api`（8000）、`/yddm-api`（YDDM），避免跨域 |
| [组件命名与注释](./component-style.md) | `defineOptions` 组件名、函数/变量/TS 注释约定（与新建任务示例对照表） |

数据库与 ORM 文档（[DATABASE.md](../DATABASE.md)）**不直接对应** `feishu/` 源码；仅在后端联调或理解数据字段时需要查阅。

---

## 消费后端 API（统一响应体）

`server/` 返回的 JSON **外层固定为** `{ code, message, data }`：

- **`code === 0`**：成功，业务数据在 **`data`**（可能是对象、数组或 `null`）。
- **`code !== 0`**：失败，请用 **`message`** 提示用户；必要时查看 **`data`**（如校验错误明细）。

工程内封装：**`feishu/src/lib/api.ts`** — `apiFetch` 解析统一信封并只返回 **`data`**；各导出函数带 **JSDoc**（对应 `docs/API.md` 路径与参数）。注释与后端路由同步要求见 **[API.md 第九节](../API.md#9-代码位置与接口注释约定)**。

其它与页面弱耦合的可复用逻辑放在 **`feishu/src/lib/*.ts`**（如任务生效/过期时间与日期控件：**`lib/datetime-task-window.ts`**）。**跨模块复用、禁止重复造轮子**的约定见 **[DEVELOPMENT.md](../DEVELOPMENT.md)** 第九节。

完整约定见 **[HTTP 接口规范](../API.md)** 第五节；飞书任务配置接口见同文档第八节。

---

## 本地运行

前端直连后端时，复制 **`feishu/.env.example`** 为 **`feishu/.env`**，按需设置 **`VITE_API_BASE_URL`**（如 `http://127.0.0.1:8000`，不含 `/api`）。**本地 `npm run dev` 未配置时**，前端默认请求 `http://127.0.0.1:8000`。打包部署到其它域名前请在 `.env` 中写入真实后端地址后再执行 `npm run build`。接口约定见 **[API.md](../API.md)**（第五节统一响应、第八节任务配置）。

```powershell
cd feishu
npm install
npm run dev
```

构建与预览：

```powershell
npm run build
npm run preview
```
