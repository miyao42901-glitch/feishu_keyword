# 飞书前端：组件命名与注释约定

## 适用范围

`feishu/src` 下 Vue 单文件组件；**页面私有组件**以 `views/<功能>/components/` 为典型。

## 1. 组件名（`defineOptions`）

- 在每个 **`.vue`** 的 `<script setup>` **首行或紧跟 import 之后** 使用 **`defineOptions({ name: 'PascalCaseName' })`**，与**文件名 PascalCase** 一致（或无 `.vue` 后缀的等价名）。
- 用途：Vue DevTools、递归组件、与其它约定对齐；页面根组件可与目录名对应，如 **`TaskCreateForm`**。

### 新建任务表单（示例对照表）

| 文件 | `name` |
|------|--------|
| `views/TaskCreateForm/index.vue` | `TaskCreateForm` |
| `views/TaskCreateForm/components/BasicInfoSection.vue` | `BasicInfoSection` |
| `views/TaskCreateForm/components/KeywordsSection.vue` | `KeywordsSection` |
| `views/TaskCreateForm/components/FilterSettingsSection.vue` | `FilterSettingsSection` |
| `views/TaskCreateForm/components/SourceSelectionSection.vue` | `SourceSelectionSection` |
| `views/TaskCreateForm/components/DataRetentionSection.vue` | `DataRetentionSection` |

## 2. 函数注释

- 非一目了然的 **`function`** 使用 **单行或块注释（中文）**，说明**职责、关键参数、副作用**。
- 事件处理器（如 `@click` 对应一行逻辑）可不写注释；**多条分支或含业务规则**须注释。

## 3. 变量与响应式注释

- **`props` / `emit` / `ref` / `reactive` / `computed`**：在声明处用简短中文说明用途；**缩写或魔法组合**必须注释。
- 与接口字段对应的模型字段，必要时在 **`types.ts`** 用 **`/** ... */`** 标注意图。

## 4. TS 模块（`types.ts`、`constants.ts`）

- **`types.ts`**：类型、接口顶上加文件级注释；导出项用 JSDoc 说明与后端/产品字段对应关系。
- **`constants.ts`**：每个导出常量分组注释；选项类说明取值含义或提交给 API 的形态。

目录结构约定仍以 **[DEVELOPMENT.md](../DEVELOPMENT.md)** 第二节为准。
