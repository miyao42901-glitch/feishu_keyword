@echo off
setlocal EnableExtensions
rem 正式环境 API 地址预编译 admin + feishu

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo [1/2] admin -^> public\admin
pushd "%ROOT%\admin" || exit /b 1
call npm run build:public:prod
if errorlevel 1 popd & exit /b 1
popd

echo [2/2] feishu -^> public\feishu
pushd "%ROOT%\feishu" || exit /b 1
call npm run build:public:prod
if errorlevel 1 popd & exit /b 1
popd

echo [OK] 已写入 public\admin 与 public\feishu，提交后由 master deploy-prod 使用
exit /b 0
