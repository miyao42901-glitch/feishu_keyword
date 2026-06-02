# 表单样式统一规范

基于抖音表单的样式结构，所有平台（快手、公众号、视频号、小红书）都应使用以下统一的样式结构。

## 1. 整体布局结构

```html
<div class="collect-panel">
  <!-- 采集内容区域 -->
  <div class="section-title">采集内容</div>
  <div class="collect-sub-panel">
    <!-- 内容区块 -->
  </div>

  <!-- 采集账号区域 -->
  <div class="section-title">
    采集账号
    <el-icon class="icon-hint" @click="openTip"><QuestionFilled /></el-icon>
  </div>
  <div class="collect-sub-panel">
    <!-- 内容区块 -->
  </div>

  <!-- 按钮区域 -->
  <div class="collect-btn-container">
    <div class="collect-btn-item">
      <el-button class="collect-btn">主要操作按钮</el-button>
    </div>
    <div class="collect-btn-item">
      <el-button class="update-btn">次要操作按钮</el-button>
    </div>
  </div>
</div>
```

## 2. 样式类说明

### 2.1 容器类
- `.collect-panel` - 最外层容器，白色背景，圆角8px
- `.collect-sub-panel` - 内容区域容器，灰色背景 #f5f6f7，圆角8px，内边距16px
- `.section-block` - 内容区块，底部间距16px

### 2.2 标题类
- `.section-title` - 区域标题，字体14px，加粗，颜色 #303133
- `.field-label` - 字段标签，字体13px，颜色 #606266

### 2.3 切换按钮类
- `.toggle-wrapper` - 切换按钮容器，白色背景，圆角6px
- `.toggle-btn` - 切换按钮，默认透明背景，激活时深蓝色 #021446
- `.toggle-btn.active` - 激活状态的切换按钮

### 2.4 操作按钮类
- `.collect-btn` - 主要操作按钮，深蓝色背景 #162042，白色文字
- `.update-btn` - 次要操作按钮，白色背景，灰色边框 #aabbcc
- `.collect-btn-container` - 按钮容器
- `.collect-btn-item` - 单个按钮项

### 2.5 输入组件类
- `.account-input-group` - 账号输入组，flex布局，间距8px
- `.account-add-btn` - 添加/删除按钮，32x32px，白色背景，灰色边框
- `.custom-select` - 自定义下拉框，宽度100%

## 3. 切换按钮示例

```html
<div class="toggle-wrapper">
  <el-button 
    type="info" 
    class="toggle-btn" 
    :class="{ active: paneData.collectionType === 'blogger' }" 
    @click="changecollectionType('blogger')"
  >
    采集博主数据
  </el-button>
  <el-button 
    type="info" 
    class="toggle-btn" 
    :class="{ active: paneData.collectionType === 'post' }" 
    @click="changecollectionType('post')"
  >
    采集作品数据
  </el-button>
</div>
```

## 4. 主要操作按钮示例

```html
<div class="collect-btn-container">
  <div class="collect-btn-item">
    <el-button
      class="collect-btn"
      :disabled="isLocked"
      @click="executeCollect(collectData)"
    >
      采集数据
    </el-button>
  </div>
  <div class="collect-btn-item">
    <el-button
      class="update-btn"
      v-if="showUpdateButton"
      :disabled="isLocked"
      @click="executeCollect(updateWorks)"
    >
      批量更新作品数据
    </el-button>
  </div>
</div>
```

## 5. 颜色规范

- 主色调（深蓝色）：#162042 / #021446
- 背景色（灰色）：#f5f6f7
- 边框色（灰色）：#dcdfe6 / #aabbcc
- 文字色（深灰）：#303133 / #606266
- 悬停色（浅灰）：#e6e8eb

## 6. 重构步骤

对于每个平台的表单，按以下步骤重构：

1. 保留所有 `<script>` 部分的业务逻辑代码
2. 将 `<template>` 部分从 `<el-form>` 结构改为 `<div class="collect-panel">` 结构
3. 将 `<el-radio-group>` 改为 `.toggle-wrapper` + `.toggle-btn`
4. 将 `<el-button type="primary">` 改为 `.collect-btn` 或 `.update-btn`
5. 确保导入了 `@/assets/form-styles.css`
6. 移除 `<style scoped>` 中的自定义样式（使用全局样式）

## 7. 注意事项

- 所有样式类都已在 `form-styles.css` 中定义，不需要在组件中添加自定义样式
- 切换按钮必须使用 `:class="{ active: 条件 }"` 来控制激活状态
- 主要操作按钮使用 `.collect-btn`，次要操作按钮使用 `.update-btn`
- 所有按钮都应该有 `:disabled="isLocked"` 属性
- 帮助图标使用 `<el-icon class="icon-hint" @click="openTip"><QuestionFilled /></el-icon>`
