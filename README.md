# 飞书关键词监控插件

## 当前项目

本项目是面向**飞书（Lark）**的**关键词监控插件**，用于在飞书生态内对关键词进行监控与相关能力扩展。

- **全称**：飞书关键词监控插件  
- **GitLab 仓库**：[http://192.168.1.200:8080/jzl/feishu_keyword/](http://192.168.1.200:8080/jzl/feishu_keyword/)

克隆示例：

```bash
git clone http://192.168.1.200:8080/jzl/feishu_keyword.git
```

## 线上部署

项目对外访问使用以下域名（生产主域名；协议以实际证书与入口为准）：

- **主域名**：[https://feishukeyword.tbpf.com](https://feishukeyword.tbpf.com)（API 路径前缀为 `/api`）
- **后台面板**：[https://feishukeyword.tbpf.com/admin](https://feishukeyword.tbpf.com/admin)

## `public` 目录约定

| 路径 | 说明 |
|------|------|
| `public/admin/` | 管理端静态资源，**随主 GitLab 仓提交**；本地编辑或构建后放入该目录，由 CI 同步到服务器，`docker compose --profile admin` 使用 `nginx` 挂载。 |
| `public/<飞书发布目录>/` | 供飞书开放平台上传的 **feishu 编译产物**；目录名可与你的独立发布仓一致（如 `feishu-keyword-dist`）。该路径**被主仓 `.gitignore` 忽略**，由 [`release.bat`](release.bat) 构建并推送到你自建的空仓（与主仓分离）。 |

## Docker 部署

- **编排文件**：仓库根目录 [`docker-compose.yml`](docker-compose.yml)（`docs/` 不再保留副本，见 [`docs/README.md`](docs/README.md)）。
- **前置**：在部署主机执行 `docker network create proxy`（与 Traefik 栈共用名为 `proxy` 的 external 网络）。
- **环境**：将 [`server/.env.example`](server/.env.example) 复制为 `server/.env`（本地）或部署机上的 `server/.env.master`（CI 会复制为 `server/.env`）；栈根还需 `cp -f server/.env .env` 供 Compose 插值 `API_PUBLIC_HOST`、`TRAEFIK_*` 等。
- **常用命令**：
  - 数据库 + 管理端 + API：`docker compose --profile db --profile admin up -d --build`
  - 仅 API（无本栈 MySQL/Redis 容器）：`docker compose up -d --build`
- **服务说明**：`mysql` 使用 `image: mysql:8.0`；`redis` 为 `redis:alpine`；`api` 由 [`server/Dockerfile`](server/Dockerfile) 构建；`admin-web` 为 `nginx:alpine`，Traefik 使用 **同域** `PathPrefix(/admin)` + **StripPrefix `/admin`** 将流量交给容器内静态根路径。

## CI/CD

- **配置**：仓库根目录 [`.gitlab-ci.yml`](.gitlab-ci.yml)。在 GitLab **CI/CD 变量**中配置 `SSH_PRIVATE_KEY`、`HOST_IP`；可选覆盖 `SSH_USER`、`SSH_PORT`、`PROD_ROOT`、`PROD_DIR`（默认值见该文件头部注释）。
- **行为**：`master` 分支在匹配 `changes` 时自动部署，否则可手动触发；通过 `rsync` 同步 `server/`、`docker-compose.yml`、`public/admin/`、`deploy/admin-static/` 到远端后在 `$PROD_ROOT` 执行 `docker compose --profile db --profile admin up -d --build`。若需重建 MySQL 容器，可设置 CI 变量 `FKW_MYSQL_FORCE_RECREATE=1`。

## `release.bat`（飞书发布仓）

在 **Windows** 仓库根目录执行，用于：在 `feishu` 下 `npm ci` + `npm run build`，将 `feishu/dist` 镜像同步到 `public\<DIST_DIR>\`，并在该目录内 `git commit` / `git push`。

- **默认**：`DIST_DIR=feishu-keyword-dist`，`RELEASE_BRANCH=main`。
- **覆盖示例**：`set DIST_DIR=my-feishu-dist&& set RELEASE_BRANCH=master&& release.bat`
- **首次**：目标目录须已为独立 Git 仓库（含 `.git`），例如在该目录 `git init` 并 `git remote add origin <空仓 URL>`，或使用 `git clone <空仓 URL> public\<DIST_DIR>`。
- **可选**：设置 `GIT_REMOTE` 后，脚本会为 `origin` 执行 `add` / `set-url`。

## 目录结构

仓库根目录主要包含以下部分：

```
feishu_keyword/
├── README.md
├── docker-compose.yml
├── .gitlab-ci.yml
├── release.bat
├── public/
│   └── admin/                # 管理端静态（提交主仓）
├── deploy/
│   └── admin-static/         # admin nginx 配置（default.conf）
├── feishu/                   # 飞书侧前端源码（Vite + Vue 3）
├── server/                   # FastAPI 后端
│   ├── Dockerfile
│   ├── .env.example
│   ├── deploy/docker/mysql-init/
│   └── app/
└── docs/                     # 补充文档；编排真源见根目录
```

说明：`feishu` 与 `server` 可分别独立安装依赖与启动；生产以 Docker 为准。
