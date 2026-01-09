@echo off
chcp 65001 >nul
echo ================================================================
echo    💬 WhatsApp AI Bot - 环境安装
echo ================================================================
echo.

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未检测到 Node.js
    echo.
    echo 请先安装 Node.js 16+ 或更高版本:
    echo https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js 已安装
node --version
echo.

REM 检查 npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：npm 不可用
    pause
    exit /b 1
)

echo ✅ npm 已安装
npm --version
echo.

echo ----------------------------------------------------------------
echo    正在安装依赖包...
echo ----------------------------------------------------------------
npm install

if errorlevel 1 (
    echo.
    echo ❌ 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo ================================================================
echo    ✅ 安装完成！
echo ================================================================
echo.
echo 📝 下一步操作：
echo.
echo    1. 确保已配置 .env 文件（项目根目录）
echo.
echo    2. 启动机器人：
echo       node bot.js
echo.
echo    3. 使用 WhatsApp 扫描二维码登录
echo.
echo ================================================================
pause


