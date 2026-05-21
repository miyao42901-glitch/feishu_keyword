@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem 将 feishu 构建产物同步到 public\feishu，并在该目录内手动 git push（GitHub 飞书发布，不走 CI）
rem 首次：git clone <GitHub空仓> public\feishu

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "TARGET=%ROOT%\public\feishu"

if not exist "%TARGET%\.git" (
  echo [ERROR] 未找到 "%TARGET%\.git"
  echo 请先: git clone ^<GitHub 空仓 URL^> "%TARGET%"
  exit /b 1
)

pushd "%ROOT%\feishu" || exit /b 1
if /i "%~1"=="prod" (
  call npm run build:public:prod
) else (
  call npm run build:public:test
)
if errorlevel 1 popd & exit /b 1
popd

echo [OK] 已写入 public\feishu ，请在 public\feishu 目录内手动 git add/commit/push
exit /b 0
