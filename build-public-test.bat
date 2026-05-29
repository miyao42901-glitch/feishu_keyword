@echo off
setlocal EnableExtensions
rem 本地预编译 admin + feishu 到 public/（可选；CI Runner 会自动 build:public:test）
rem 测试环境一键构建；正式环境用 build-public-prod.bat

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo [0/2] 使用 .env.test 覆盖 .env（Vite envDir=仓根）
copy /Y "%ROOT%\.env.test" "%ROOT%\.env" >nul
if errorlevel 1 (
  echo ERROR: 缺少 %ROOT%\.env.test
  exit /b 1
)

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

echo [OK] 已写入 public\admin 与 public\feishu（本地预检；推 test 后由 CI Runner 编译部署）
exit /b 0
