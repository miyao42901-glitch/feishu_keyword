@echo off
setlocal EnableExtensions
rem 本地预编译 admin + feishu 到 public/（GitLab CI 仅 rsync，Runner 无需 Node）
rem 用法: build-public-test.bat
rem 正式: build-public-prod.bat

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo [1/2] admin -^> public\admin
pushd "%ROOT%\admin" || exit /b 1
call npm run build:public:test
if errorlevel 1 popd & exit /b 1
popd

echo [2/2] feishu -^> public\feishu
pushd "%ROOT%\feishu" || exit /b 1
call npm run build:public:test
if errorlevel 1 popd & exit /b 1
popd

echo [OK] 已写入 public\admin 与 public\feishu，请 git add/commit 后推送以触发 deploy-test
exit /b 0
