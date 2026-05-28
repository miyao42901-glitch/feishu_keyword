@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem 将 feishu 构建产物同步到 public\feishu\dist（GitHub 仓结构：dist/ + package.json），再手动 git push
rem 首次：git clone <GitHub空仓> public\feishu
rem Docker 扁平目录请用 feishu 目录下 npm run build:public:test

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
  call npm run build:github:prod
) else (
  call npm run build:github:test
)
if errorlevel 1 popd & exit /b 1
popd

echo [OK] 已写入 public\feishu\dist ，请在 public\feishu 目录内手动 git add/commit/push
exit /b 0
