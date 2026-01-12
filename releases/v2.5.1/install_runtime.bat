@echo off
chcp 65001 >nul
echo ================================================
echo    AI Talk - 运行环境安装脚本
echo ================================================
echo.
echo 将创建 Python 3.13 虚拟环境并安装依赖
echo.

set VENV_DIR=venv313
set PY_EXE="%VENV_DIR%\Scripts\python.exe"

REM 创建虚拟环境
if not exist %PY_EXE% (
  echo 正在创建虚拟环境: %VENV_DIR%
  py -3.13 -m venv %VENV_DIR%
)

echo 正在安装依赖...
%PY_EXE% -m pip install --upgrade pip
%PY_EXE% -m pip install -r requirements.txt

echo.
echo ✅ 运行环境安装完成
echo - 虚拟环境: %VENV_DIR%
echo - 后续可运行: scripts\start_admin.bat 或 scripts\start_multi_admin.bat
echo.
pause

