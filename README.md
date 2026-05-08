# 飞书关键词监控插件

## 当前项目

本项目是面向**飞书（Lark）**的**关键词监控插件**，用于在飞书生态内对关键词进行监控与相关能力扩展。

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
└── docs/                     # 技术文档（入口 docs/README.md；按 server/feishu 见 docs/server、docs/feishu）
```

说明：`feishu` 与 `server` 可分别独立安装依赖与启动；具体启动命令以各子目录内配置为准。
