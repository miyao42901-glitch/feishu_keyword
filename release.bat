@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem 用法：在仓库根目录执行 release.bat
rem 可选环境变量：DIST_DIR（默认 feishu-keyword-dist）、RELEASE_BRANCH（默认 main）、GIT_REMOTE（若需设置 origin）

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if not defined DIST_DIR set "DIST_DIR=feishu-keyword-dist"
if not defined RELEASE_BRANCH set "RELEASE_BRANCH=main"

set "TARGET=%ROOT%\public\%DIST_DIR%"

if not exist "%TARGET%\.git" (
  echo [ERROR] 未找到 "%TARGET%\.git"。
  echo 请先在独立空仓中初始化该目录，例如：
  echo   mkdir public\%DIST_DIR%  ^&^& cd public\%DIST_DIR%
  echo   git init
  echo   git remote add origin ^<你的空仓 HTTPS/SSH URL^>
  echo 或：git clone ^<空仓 URL^> "%TARGET%"
  exit /b 1
)

if defined GIT_REMOTE (
  pushd "%TARGET%" || exit /b 1
  git remote get-url origin >nul 2>&1
  if errorlevel 1 (
    git remote add origin "%GIT_REMOTE%"
  ) else (
    git remote set-url origin "%GIT_REMOTE%"
  )
  popd
)

pushd "%ROOT%\feishu" || exit /b 1
call npm ci
if errorlevel 1 popd & exit /b 1
call npm run build
if errorlevel 1 popd & exit /b 1
popd

if not exist "%ROOT%\feishu\dist\" (
  echo [ERROR] 未找到 feishu\dist，构建是否失败？
  exit /b 1
)

robocopy "%ROOT%\feishu\dist" "%TARGET%" /MIR /NFL /NDL /NJH /NJS /NC /NS
set "RC=%ERRORLEVEL%"
if %RC% GEQ 8 (
  echo [ERROR] robocopy 失败，代码 %RC%
  exit /b 1
)

pushd "%TARGET%" || exit /b 1
git add -A
git diff --staged --quiet
if errorlevel 1 (
  git commit -m "build: feishu dist %date% %time%"
  if errorlevel 1 popd & exit /b 1
) else (
  echo [INFO] 无变更可提交，仍将尝试 push。
)
git push -u origin "%RELEASE_BRANCH%"
if errorlevel 1 popd & exit /b 1
popd

echo [OK] 已构建并推送到 origin/%RELEASE_BRANCH% ，目录：public\%DIST_DIR%
exit /b 0
