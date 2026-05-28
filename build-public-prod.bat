@echo off
setlocal EnableExtensions
rem 正式环境 API 预编译 admin + feishu

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo [0/2] 使用 .env.master 覆盖 .env（Vite envDir=仓根）
copy /Y "%ROOT%\.env.master" "%ROOT%\.env" >nul
if errorlevel 1 (
  echo ERROR: 缺少 %ROOT%\.env.master
  exit /b 1
)

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

echo [OK] 已写入 public\admin 与 public\feishu，提交后 MR 合并 master，在流水线手动运行 deploy-prod
exit /b 0
