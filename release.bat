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

rem 自动检测分支：master → prod，其他 → test；可手动覆盖 release.bat prod|test
set "BUILD_ENV=%~1"
if "%BUILD_ENV%"=="" (
  for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "CURRENT_BRANCH=%%i"
  if "!CURRENT_BRANCH!"=="master" (
    set "BUILD_ENV=prod"
    echo [INFO] 检测到 master 分支，使用正式环境（prod）
  ) else (
    set "BUILD_ENV=test"
    echo [INFO] 检测到 !CURRENT_BRANCH! 分支，使用测试环境（test）
  )
)

echo [INFO] 构建环境：%BUILD_ENV%

pushd "%ROOT%\feishu" || exit /b 1
if /i "%BUILD_ENV%"=="prod" (
  call npm run build:github:prod
) else (
  call npm run build:github:test
)
if errorlevel 1 popd & exit /b 1
popd

echo [OK] 已写入 public\feishu\dist ，请在 public\feishu 目录内手动 git add/commit/push
exit /b 0
