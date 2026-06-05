# 飞书插件部署域名配置说明

本文档说明飞书插件在不同场景下的 API 域名配置和推送流程。

## 三种部署场景

### 1. 本地开发（使用本机 IP）

**环境文件**：`.env.local`（Git 忽略，不提交）

**配置示例**：
```env
VITE_YDDM_API_BASE=
VITE_SYNC_API_BASE=http://192.168.1.24:8765
```

**说明**：
- `VITE_YDDM_API_BASE` 留空，使用相对路径 `/yddm-api`，由 Vite 开发服务器代理
- `VITE_SYNC_API_BASE` 指向本机或局域网 IP
- 此文件优先级最高，会覆盖 `.env` 中的配置

**启动方式**：
```powershell
cd feishu
npm run dev          # 本机访问
npm run dev:lan      # 局域网访问
```

---

### 2. GitLab CI 自动部署（Docker 环境）

#### 2.1 test 分支 → 测试环境

**触发条件**：推送到 `test` 分支

**环境文件**：`.env.test`

**API 域名配置**：
```env
VITE_YDDM_API_BASE=https://test-fskw-feishu.tbpf.com/yddm-api
VITE_SYNC_API_BASE=https://test-fskw-feishu.tbpf.com
```

**部署目标**：
- 服务器路径：`/docker/feishu_keyword-test`
- 公网域名：`https://test-fskw-feishu.tbpf.com`

**推送命令**：
```powershell
git add .
git commit -m "feat: 你的改动说明"
git push origin test
```

推送后 GitLab CI 会自动触发 `deploy-test` 流水线。

#### 2.2 master 分支 → 正式环境

**触发条件**：合并到 `master` 分支

**环境文件**：`.env.master`

**API 域名配置**：
```env
VITE_YDDM_API_BASE=https://fskw-feishu.tbpf.com/yddm-api
VITE_SYNC_API_BASE=https://fskw-feishu.tbpf.com
```

**部署目标**：
- 服务器路径：`/docker/feishu_keyword`
- 公网域名：`https://fskw-feishu.tbpf.com`

**推送流程**：
```powershell
# 1. 在 test 分支开发完成后，本地合并到 master
git checkout master
git merge test

# 2. 推送到 GitLab
git push origin master

# 3. 在 GitLab Web UI 手动触发 deploy-prod 流水线
```

---

### 3. GitHub CDN 发版（飞书插件商店）

**触发条件**：手动执行 `release.bat`

**API 域名配置**：固定使用正式域名
```env
VITE_YDDM_API_BASE=https://fskw-feishu.tbpf.com/yddm-api
VITE_SYNC_API_BASE=https://fskw-feishu.tbpf.com
GITHUB_REPO=git@github.com:miyao42901-glitch/feishu_keyword.git
```

**CDN 访问域名**：`ext.baseopendev.com`（飞书 CDN）

**推送命令**：
```powershell
# 在仓库根目录执行（不管在哪个分支）
release.bat
```

**工作流程**：
1. 临时重命名 `.env.local` 避免干扰
2. 写入正式域名到 `.env`
3. 构建 dist 包（`npm run build:github:prod`）
4. 推送到 GitHub 仓库 `main` 分支
5. 还原 `.env.local`

**注意事项**：
- GitHub 发版永远使用正式域名，不管当前在哪个分支
- 飞书会从 GitHub 拉取静态文件，通过 `ext.baseopendev.com` 分发
- 用户访问插件后，API 请求打到 `https://fskw-feishu.tbpf.com`

---

## 快速参考表

| 场景 | 环境文件 | API 域名 | 推送目标 | 触发方式 |
|------|---------|---------|---------|---------|
| 本地开发 | `.env.local` | 本机 IP | - | `npm run dev` |
| GitLab 测试 | `.env.test` | `test-fskw-feishu.tbpf.com` | GitLab `test` | `git push origin test` |
| GitLab 正式 | `.env.master` | `fskw-feishu.tbpf.com` | GitLab `master` | `git push origin master` |
| GitHub CDN | 构建时注入 | `fskw-feishu.tbpf.com` | GitHub `main` | `release.bat` |

---

## 常见问题

### Q1: 本地开发时 API 请求 404？

**原因**：`.env.local` 中的 `VITE_SYNC_API_BASE` 配置错误或后端未启动。

**解决**：
1. 检查后端是否启动：`cd server && python run.py`
2. 确认 `.env.local` 中的 IP 地址正确
3. 如果局域网联调，确保防火墙允许 8765 端口

### Q2: GitLab CI 构建后仍然请求错误的域名？

**原因**：`.env.test` 或 `.env.master` 中的配置不正确。

**解决**：
1. 检查对应环境文件中的 `VITE_YDDM_API_BASE` 和 `VITE_SYNC_API_BASE`
2. 确认 CI 脚本 `scripts/ci-build-frontend.sh` 正确复制了环境文件
3. 查看 GitLab CI 日志确认构建使用的环境变量

### Q3: GitHub CDN 发版后插件仍然请求 `ext.baseopendev.com`？

**原因**：构建时 `.env.local` 覆盖了正式域名配置。

**解决**：
- 使用 `release.bat` 而不是手动构建，它会自动处理 `.env.local` 的临时移除
- 如果手动构建，需要先临时重命名 `.env.local`

### Q4: 如何验证构建产物中的域名是否正确？

```powershell
# 在构建产物中搜索域名
Select-String -Pattern "fskw-feishu|test-fskw" -Path "public\feishu\dist\assets\*.js"
```

应该能找到对应环境的域名字符串。

---

## 文件说明

### 环境文件优先级（从高到低）

1. `.env.local` - 本地开发专用（不提交 Git）
2. `.env` - 临时构建文件（不提交 Git）
3. `.env.test` - 测试环境模板（提交 Git）
4. `.env.master` - 正式环境模板（提交 Git）

### 关键脚本

- `release.bat` - GitHub CDN 发版脚本（构建 + 推送）
- `scripts/ci-build-frontend.sh` - GitLab CI 构建脚本
- `feishu/vite.config.ts` - Vite 配置，`envDir` 指向仓库根目录

---

## 最佳实践

1. **本地开发**：
   - 使用 `.env.local` 配置本机 IP
   - 不要提交 `.env.local` 到 Git

2. **测试新功能**：
   - 在 `test` 分支开发
   - 推送后自动部署到测试环境
   - 测试通过后再合并到 `master`

3. **正式发版**：
   - 先合并 `test` 到 `master`
   - 推送到 GitLab，手动触发 `deploy-prod`
   - Docker 环境验证通过后，再执行 `release.bat` 发布到 GitHub CDN

4. **紧急修复**：
   - 可以直接在 `master` 分支修改
   - 修改后同时推送 GitLab 和 GitHub
   - 记得回头合并到 `test` 分支保持一致

---

## 相关文档

- [前端开发规范](./feishu/README.md)
- [Nginx 反向代理配置](./feishu/NGINX.md)
- [Git 工作流程](./GIT_WORKFLOW.md)
- [部署流程](./DEPLOY.md)
