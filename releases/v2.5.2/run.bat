@echo off
chcp 65001 >nul
title Telegram AI Bot
echo ================================================================
echo    🤖 Telegram AI Bot - 启动程序
echo ================================================================
echo.

REM Select Python Interpreter
if exist ".\.venv313\Scripts\python.exe" (
  set "PYTHON_EXE=.\.venv313\Scripts\python.exe"
) else if exist ".\venv313\Scripts\python.exe" (
  set "PYTHON_EXE=.\venv313\Scripts\python.exe"
) else (
  set "PYTHON_EXE=python"
)

REM 检查 Python
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先运行 install.bat 进行安装配置。
    pause
    exit /b 1
)

REM 检查 .env
if not exist .env (
    if exist .env.example (
        echo ⚠️ 首次运行，正在初始化配置文件...
        copy .env.example .env >nul
    )
)

REM 自动检查并安装依赖
echo 🔍 正在检查核心依赖...
"%PYTHON_EXE%" -c "import PyPDF2, docx, openpyxl, telethon, openai" >nul 2>&1
if errorlevel 1 (
    echo 📦 检测到缺失依赖，正在自动补全...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 自动安装依赖失败。
        echo 请尝试手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo ✅ 依赖补全成功
)

echo 🚀 正在启动机器人核心...
echo 💡 提示：如果是首次运行，请按屏幕提示输入 Telegram 手机号进行登录。
echo.
"%PYTHON_EXE%" main.py

if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出
    pause
)
