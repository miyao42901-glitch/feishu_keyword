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

---

## 与本目录相关的规范文档

| 文档 | 说明 |
|------|------|
| [工程约定](../DEVELOPMENT.md) | 全仓库 Git、注释、环境安全 |
| [HTTP 接口规范](../API.md) | 若前端直连 **`server/`** 提供的 API，须遵守路径与分页等约定；**API Base URL 可配置，禁止写死生产地址** |

数据库与 ORM 文档（[DATABASE.md](../DATABASE.md)）**不直接对应** `feishu/` 源码；仅在后端联调或理解数据字段时需要查阅。

---

## 本地运行

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
