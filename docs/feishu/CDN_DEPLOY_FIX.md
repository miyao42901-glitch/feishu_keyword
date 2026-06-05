# 飞书插件 CDN 部署问题修复指南

## 问题描述

### 问题 1：404 错误
部署到飞书 CDN（`ext.baseopendev.com`）后，请求到错误的 API 地址：
```
Request URL: https://ext.baseopendev.com/yddm-api/users/me
Status Code: 404 Not Found
```

**原因**：构建时未正确注入 `VITE_YDDM_API_BASE` 和 `VITE_SYNC_API_BASE` 环境变量，导致前端代码使用相对路径 `/yddm-api`，被浏览器解析为 CDN 域名下的路径。

### 问题 2：白屏需要刷新
首次打开插件为白屏，刷新浏览器后才能正常显示。

**原因**：应用启动时自动调用 `GET /users/me` 初始化用户信息，由于问题 1 导致该请求 404 失败，造成初始化异常。

---

## 根本原因分析

飞书插件有两种部署方式：

### 1. Docker 同源部署（`fskw-feishu.tbpf.com`）
- Nginx 反向代理 `/yddm-api/` → `https://api.yddm.com`
- 前端可以使用相对路径 `/yddm-api`
- **不需要**在构建时设置 `VITE_YDDM_API_BASE`

### 2. 飞书 CDN 部署（`ext.baseopendev.com`）
- 静态资源托管在飞书 CDN，**没有** Nginx 反向代理
- 前端**必须**使用绝对路径指向你的服务器
- **必须**在构建时设置 `VITE_YDDM_API_BASE` 和 `VITE_SYNC_API_BASE`

当前问题出在：**GitHub 发版（CDN 部署）时，构建环境中的 `.env` 文件缺失或配置不正确**。

---

## 解决方案

### 自动化修复（已完成）

`release.bat` 已修改为**自动检测 Git 分支**：
- **master 分支**：自动使用 `.env.master`（正式域名 `fskw-feishu.tbpf.com`）
- **其他分支**：自动使用 `.env.test`（测试域名 `test-fskw-feishu.tbpf.com`）
- **手动覆盖**：可用 `release.bat prod` 或 `release.bat test` 强制指定环境

### 飞书插件 CDN 发版流程

#### 方式 1：使用 release.bat（推荐）

```powershell
# 在仓库根目录执行，自动检测分支
cd d:\project\feishu_keyword
release.bat

# 或手动指定环境
release.bat prod    # 强制使用正式环境
release.bat test    # 强制使用测试环境
```

#### 方式 2：使用 npm scripts

```powershell
cd d:\project\feishu_keyword

# 确保 .env 正确配置
cp .env.master .env    # 正式环境
# 或
cp .env.test .env      # 测试环境

cd feishu

# 构建并推送
npm run release:plugin-static:prod    # 正式环境
# 或
npm run release:plugin-static:test    # 测试环境
```

### 验证构建产物

检查构建后的 `public/feishu/dist/` 目录，确认 JavaScript 中包含正确的 API 地址：

```powershell
# 正式环境应包含正式域名
cd public\feishu\dist\assets
Select-String -Pattern "fskw-feishu.tbpf.com" *.js

# 测试环境应包含测试域名
Select-String -Pattern "test-fskw-feishu.tbpf.com" *.js
```

---

## 完整发布流程（推荐）

### 测试环境完整流程
```powershell
# 1. 进入仓库根目录
cd d:\project\feishu_keyword

# 2. 复制测试环境配置
cp .env.test .env

# 3. 进入前端目录
cd feishu

# 4. 构建并发布
npm run build:github:test
npm run push:plugin-static

# 5. 验证（可选）
cd dist
Select-String -Pattern "test-fskw-feishu.tbpf.com" -Path "*.js"
```

### 正式环境完整流程
```powershell
# 1. 进入仓库根目录
cd d:\project\feishu_keyword

# 2. 复制正式环境配置
cp .env.master .env

# 3. 进入前端目录
cd feishu

# 4. 构建并发布
npm run build:github:prod
npm run push:plugin-static

# 5. 验证（可选）
cd dist
Select-String -Pattern "fskw-feishu.tbpf.com" -Path "*.js"
```

---

## 验证修复

### 1. 浏览器开发者工具检查
打开飞书插件后，按 F12 打开开发者工具：

**Network 标签页**：
- 查看 `/users/me` 请求
- ✅ 正确：`https://test-fskw-feishu.tbpf.com/yddm-api/users/me`
- ❌ 错误：`https://ext.baseopendev.com/yddm-api/users/me`

**Console 标签页**：
- 不应该有 404 错误
- 不应该有 CORS 错误

### 2. 功能验证
- ✅ 首次打开插件正常显示（不再白屏）
- ✅ 登录功能正常
- ✅ 任务列表加载正常
- ✅ 创建任务功能正常

---

## 注意事项

### 1. 本地开发不受影响
本地开发时（`npm run dev`），Vite 会使用内置代理，**不需要**设置 `VITE_YDDM_API_BASE`。

可以在 `.env.local` 中清空这些变量：
```env
# .env.local（本地开发专用，不提交到 Git）
VITE_YDDM_API_BASE=
VITE_SYNC_API_BASE=
```

### 2. Docker 部署不受影响
Docker 部署（`fskw-feishu.tbpf.com`）有 Nginx 反向代理，即使设置了 `VITE_YDDM_API_BASE` 为绝对路径也兼容。

### 3. 环境变量优先级
Vite 环境变量加载顺序（优先级从高到低）：
1. `.env.local`（本地开发，不提交）
2. `.env`（构建时使用，不提交）
3. `.env.test` / `.env.master`（配置模板，提交到 Git）

### 4. CI/CD 流程
如果使用 GitLab CI 自动构建，需要在 `.gitlab-ci.yml` 中添加：

```yaml
build-feishu-github:
  stage: build
  script:
    - cp .env.test .env  # 或 .env.master
    - cd feishu
    - npm ci
    - npm run build:github:test
    - npm run push:plugin-static
  only:
    - master
```

---

## 故障排查

### 问题：构建后仍然是相对路径
**检查**：
```powershell
cd d:\project\feishu_keyword
Get-Content .env | Select-String "VITE_YDDM_API_BASE"
```

**解决**：
- 确认 `.env` 文件存在且包含正确配置
- 确认 `VITE_YDDM_API_BASE` 不为空
- 重新运行 `npm run build:github:test`

### 问题：仍然出现 CORS 错误
**检查**：
- 确认服务器 Nginx 配置中 `/yddm-api/` location 包含 CORS 头
- 查看 `deploy/feishu-static/default.conf` 中的 CORS 配置

**解决**：
确保 Nginx 配置包含：
```nginx
location /yddm-api/ {
    if ($request_method = OPTIONS) {
        add_header Access-Control-Allow-Origin $http_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept" always;
        add_header Access-Control-Max-Age 86400 always;
        add_header Content-Length 0;
        return 204;
    }
    add_header Access-Control-Allow-Origin $http_origin always;
    # ...
}
```

### 问题：白屏但控制台无错误
**检查**：
- 查看 Console 是否有 JavaScript 错误
- 查看 Network 是否有资源加载失败（404/500）

**解决**：
- 确认所有静态资源路径正确（`base: './'`）
- 清除浏览器缓存后重试

---

## 相关文档

- [NGINX.md](./NGINX.md) - Nginx 反向代理配置详解
- [README.md](./README.md) - 前端技术栈与开发规范
- [HTTP_API.md](../server/HTTP_API.md) - 后端 API 接口文档
- [DEPLOY.md](../DEPLOY.md) - 完整部署流程
