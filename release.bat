@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem 将 feishu 构建产物同步到 public\feishu\dist，并强制推送到 GitHub 插件发布仓
rem GitHub CDN 发版固定使用正式域名 fskw-feishu.tbpf.com
rem 首次：git clone <GitHub空仓> public\feishu

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "TARGET=%ROOT%\public\feishu"

if not exist "%TARGET%\.git" (
  echo [ERROR] 未找到 "%TARGET%\.git"
  echo 请先: git clone ^<GitHub 空仓 URL^> "%TARGET%"
  exit /b 1
)

echo [INFO] GitHub CDN 发版，固定使用正式域名 fskw-feishu.tbpf.com

(
  echo VITE_YDDM_API_BASE=https://fskw-feishu.tbpf.com/yddm-api
  echo VITE_SYNC_API_BASE=https://fskw-feishu.tbpf.com
  echo GITHUB_REPO=git@github.com:miyao42901-glitch/feishu_keyword.git
) > "%ROOT%\.env"
echo [INFO] 已写入 .env

rem .env.local 优先级高于 .env，构建期间临时改名，防止覆盖 VITE 变量
set "ENV_LOCAL=%ROOT%\.env.local"
set "ENV_LOCAL_BAK=%ROOT%\.env.local.release-bak"
if exist "%ENV_LOCAL%" (
  rename "%ENV_LOCAL%" ".env.local.release-bak"
  echo [INFO] 已临时重命名 .env.local
)

pushd "%ROOT%\feishu"
if errorlevel 1 (
  if exist "%ENV_LOCAL_BAK%" rename "%ENV_LOCAL_BAK%" ".env.local"
  exit /b 1
)

call npm run build:github:prod
set "BUILD_EXIT=%ERRORLEVEL%"
popd

if exist "%ENV_LOCAL_BAK%" (
  rename "%ENV_LOCAL_BAK%" ".env.local"
  echo [INFO] 已还原 .env.local
)

if %BUILD_EXIT% neq 0 (
  echo [ERROR] 构建失败
  exit /b %BUILD_EXIT%
)

echo [INFO] 构建成功，推送到 GitHub...
pushd "%ROOT%\feishu"
set "GITHUB_REPO=git@github.com:miyao42901-glitch/feishu_keyword.git"
call npm run push:plugin-static
set "PUSH_EXIT=%ERRORLEVEL%"
popd

if %PUSH_EXIT% neq 0 (
  echo [ERROR] 推送失败
  exit /b %PUSH_EXIT%
)

echo [OK] dist 包已构建并推送到 GitHub（正式域名：fskw-feishu.tbpf.com）
exit /b 0
