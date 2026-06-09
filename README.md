# 飞书关键词监控插件

## 当前项目

本项目是面向**飞书（Lark）**的**关键词监控插件**，用于在飞书生态内对关键词进行监控与相关能力扩展的。 

- **全称**：飞书关键词监控插件  
- **GitLab 仓库**：[http://192.168.1.200:8080/jzl/feishu_keyword/](http://192.168.1.200:8080/jzl/feishu_keyword/)

克隆示例：

```bash
git clone http://192.168.1.200:8080/jzl/feishu_keyword.git
```

## 目录结构

仓库根目录主要包含以下部分：

```
feishu_keyword/
├── README.md                 # 本说明
├── feishu/                   # 飞书侧前端（插件 / 多维表格等前端工程）
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig*.json
│   ├── public/               # 静态资源（如图标）
│   └── src/                  # 源码（Vue 3、页面与业务逻辑等）
├── server/                   # 后端服务（Python + FastAPI）
│   ├── requirements.txt      # Python 依赖
│   ├── app/
│   │   ├── main.py           # FastAPI 应用入口
│   │   └── api/              # 路由与接口实现
│   └── .venv/                # 本地虚拟环境（勿提交，见各目录 .gitignore）
├── python/                   # 统一 HTTP + Celery 异步采集（与 server、feishu 无代码耦合）
│   ├── run.py                # FastAPI 入口
│   ├── HTTP_API.md           # 接口说明
│   └── DEPLOYMENT.md         # FastAPI / Celery 启动与生产部署
└── docs/                     # 项目文档（设计说明、接口约定等，可按需补充）
```

说明：`feishu` 与 `server` 可分别独立安装依赖与启动。异步采集需同时启动 **`python/run.py`** 与 **Celery Worker**，详见 [`python/DEPLOYMENT.md`](python/DEPLOYMENT.md)。
