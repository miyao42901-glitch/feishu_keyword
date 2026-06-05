# 埋点功能说明

## 功能概述

本项目新增了完整的数据埋点看板功能,用于监控和分析用户行为、任务执行、API调用等核心指标。目前使用 Mock 数据进行演示。

## 功能模块

### 1. 数据概览
- **核心KPI指标**: 活跃任务数、执行成功率、API成功率、点数消耗、用户留存率等
- **趋势图表**: 用户与业务趋势、任务状态分布、平台API调用分布、点数消耗Top用户
- **转化漏斗**: 从首页访问到任务创建的完整转化路径分析

### 2. 执行监控
- 任务执行记录列表
- 执行成功率统计
- 平均执行耗时分析
- 失败原因追踪

### 3. API监控
- API调用次数统计
- 各平台成功率对比
- 响应耗时分析
- 错误码追踪

### 4. 推送监控
- 推送记录管理
- 推送触达率统计
- 回调结果追踪
- 重试次数监控

### 5. 用户管理
- 用户列表与筛选
- 用户详情查看
- 运营备注编辑
- 用户行为分析

## 文件结构

```
src/
├── api/
│   └── analytics.js              # 埋点API接口(含Mock开关)
├── mock/
│   └── analyticsData.js          # Mock数据定义
├── views/
│   └── analytics/
│       ├── AnalyticsView.vue            # 埋点功能主入口
│       ├── AnalyticsOverviewView.vue    # 数据概览页
│       ├── ExecMonitorView.vue          # 执行监控页
│       ├── ApiMonitorView.vue           # API监控页
│       ├── PushMonitorView.vue          # 推送监控页
│       └── UserManageView.vue           # 用户管理页
└── assets/
    └── analytics.css             # 埋点页面样式
```

## 使用方法

### 在现有项目中集成

1. **添加导航入口**

在 `Form.vue` 或其他主组件中添加埋点功能的入口:

```vue
<template>
  <div>
    <!-- 现有内容 -->
    <el-button @click="showAnalytics = true">数据埋点</el-button>
    
    <!-- 埋点功能弹窗 -->
    <el-dialog v-model="showAnalytics" title="数据埋点看板" width="95%" fullscreen>
      <AnalyticsView />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AnalyticsView from '@/views/analytics/AnalyticsView.vue'

const showAnalytics = ref(false)
</script>
```

2. **作为独立Tab使用**

也可以将 `AnalyticsView` 作为新的Tab加入到现有的Tab系统中:

```vue
<el-tab-pane label="数据埋点">
  <AnalyticsView />
</el-tab-pane>
```

### 切换真实API

在 `src/api/analytics.js` 中修改 `USE_MOCK` 常量:

```javascript
const USE_MOCK = false // 改为 false 使用真实API
```

## 技术栈

- **Vue 3**: 组件框架
- **Element Plus**: UI组件库
- **ECharts 5**: 数据可视化图表
- **Axios**: HTTP请求库

## Mock数据说明

当前所有数据均为Mock数据,用于演示功能。Mock数据包括:

- 今日/本周/本月三个时间维度的数据
- 完整的用户、任务、执行记录、API调用记录等
- 模拟的转化漏斗和流失分析

## 后续开发

1. **接入真实API**
   - 修改 `src/api/analytics.js` 中的API端点
   - 确保后端返回的数据结构与Mock数据一致

2. **增强功能**
   - 添加日期范围选择器
   - 增加数据导出功能
   - 添加更多维度的数据分析
   - 实时数据刷新

3. **性能优化**
   - 图表懒加载
   - 数据分页优化
   - 请求缓存策略

## 安装依赖

如果是新环境,需要安装ECharts依赖:

```bash
npm install
```

依赖已添加到 `package.json`:
- echarts: ^5.6.0

## 运行项目

```bash
npm run dev
```

访问埋点功能页面即可看到完整的数据看板。
