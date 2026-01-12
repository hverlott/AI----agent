@echo off
chcp 65001 >nul
echo ================================================================
echo    💬 WhatsApp AI Bot
echo ================================================================
echo.
echo 正在启动 WhatsApp 机器人...
echo.
echo 提示：
echo - 首次运行需要扫描二维码登录
echo - 按 Ctrl+C 可停止运行
echo - 不要关闭此窗口
echo ================================================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到 Node.js 环境
    echo 请先安装 Node.js (推荐 v16+): https://nodejs.org/
    echo 安装完成后，请重新运行此脚本。
    pause
    exit /b 1
)

REM Check if dependencies are installed
if not exist "node_modules" (
    echo 📦 检测到依赖未安装，正在自动安装...
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败，请检查网络或手动运行 npm install
        pause
        exit /b 1
    )
)

echo 🚀 正在启动 WhatsApp 机器人...
node bot.js

pause


