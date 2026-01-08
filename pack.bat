@echo off
chcp 65001 >nul
echo ================================================================
echo    📦 Telegram AI Bot - 项目打包工具
echo ================================================================
echo.
echo 正在打包项目文件...
echo.

REM 设置打包文件名（带日期）
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%a%%b%%c)
set PACKAGE_NAME=AI-Talk-Package-%mydate%.zip

echo 📝 打包文件列表：
echo    ✓ 核心程序 (*.py)
echo    ✓ 配置文件 (*.txt, .env.example)
echo    ✓ 启动脚本 (*.bat, *.sh)
echo    ✓ 文档文件 (*.md)
echo.
echo ❌ 排除文件：
echo    ✗ .env
echo    ✗ *.session
echo    ✗ bot.pid
echo    ✗ bot.log
echo    ✗ __pycache__
echo.

REM 创建临时目录
set TEMP_DIR=AI-Talk-Package
if exist %TEMP_DIR% rmdir /s /q %TEMP_DIR%
mkdir %TEMP_DIR%

REM 复制文件
echo 正在复制文件...
copy *.py %TEMP_DIR%\ >nul 2>&1
copy *.txt %TEMP_DIR%\ >nul 2>&1
copy *.bat %TEMP_DIR%\ >nul 2>&1
copy *.sh %TEMP_DIR%\ >nul 2>&1
copy *.md %TEMP_DIR%\ >nul 2>&1
copy .env.example %TEMP_DIR%\ >nul 2>&1

REM 创建 ZIP 文件
echo 正在压缩...
powershell Compress-Archive -Path %TEMP_DIR% -DestinationPath %PACKAGE_NAME% -Force

REM 清理临时目录
rmdir /s /q %TEMP_DIR%

REM 获取文件大小
for %%A in (%PACKAGE_NAME%) do set SIZE=%%~zA
set /a SIZE_KB=%SIZE%/1024

echo.
echo ================================================================
echo    ✅ 打包完成！
echo ================================================================
echo.
echo 📦 文件名: %PACKAGE_NAME%
echo 📊 大小: %SIZE_KB% KB
echo 📍 位置: %CD%\%PACKAGE_NAME%
echo.
echo 💡 提示：
echo    - 此压缩包不包含敏感文件 (.env, *.session)
echo    - 可以安全地分享或部署到新电脑
echo    - 解压后运行 install.bat 自动安装
echo.
echo ================================================================
pause


