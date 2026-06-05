# 多平台数据采集插件 - 管理后台

这是一个独立的管理后台项目，用于展示数据采集插件的埋点数据和运营分析。

## 功能特性

### 🎯 数据总览
- 5个核心KPI指标卡片（有效用户、调用次数、消耗金额、成功率、平均时长）
- 各平台数据采集分布横向条形图
- 采集失败原因分布横向条形图
- 任务漏斗图（从打开插件到采集成功）
- 支持今日/本周/本月三个时间维度切换

### 📊 其他模块（待开发）
- 登录与进入
- 采集任务
- 帮助与引导
- 任务列表

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 UI 组件库
- **ECharts 5** - 数据可视化图表库
- **Vite** - 下一代前端构建工具
- **Axios** - HTTP 客户端

## 开发指南

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5101

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
admin/
├── src/
│   ├── api/              # API接口
│   │   └── analytics.js  # 埋点数据API（含Mock开关）
│   ├── assets/           # 静态资源
│   │   └── styles.css    # 全局样式
│   ├── mock/             # Mock数据
│   │   └── analyticsData.js
│   ├── views/            # 页面组件
│   │   ├── AnalyticsView.vue        # 主布局（左侧导航）
│   │   ├── AnalyticsOverviewView.vue # 数据总览
│   │   ├── LoginTrackView.vue       # 登录与进入
│   │   ├── CollectTaskView.vue      # 采集任务
│   │   ├── HelpGuideView.vue        # 帮助与引导
│   │   └── TaskListView.vue         # 任务列表
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## 数据说明

当前所有数据均为Mock数据，用于演示功能。

### 切换真实API

在 `src/api/analytics.js` 中修改 `USE_MOCK` 常量：

```javascript
const USE_MOCK = false // 改为 false 使用真实API
```

## 设计特点

- 🎨 深色侧边栏 + 浅色主题，现代化设计风格
- 📱 响应式布局，支持不同屏幕尺寸
- 📊 ECharts 图表展示，数据可视化清晰直观
- ⚡ Mock数据快速演示，无需后端即可查看效果

## 开发计划

- [x] 数据总览页面
- [ ] 登录与进入跟踪
- [ ] 采集任务监控
- [ ] 帮助与引导分析
- [ ] 任务列表管理
- [ ] 接入真实API
- [ ] 数据导出功能
- [ ] 实时数据刷新

## License

MIT
