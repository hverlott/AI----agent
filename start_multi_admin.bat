@echo off
chcp 65001 >nul
echo ================================================================
echo    🌐 AI Social Bot - 多平台管理中心
echo ================================================================
echo.
echo 正在启动多平台管理后台...
echo 浏览器将自动打开：http://localhost:8501
echo.
echo 支持的平台：
echo   📱 Telegram     - 完整功能
echo   💬 WhatsApp     - 开发中
echo   📘 Facebook     - 规划中
echo   💙 Messenger    - 规划中
echo   💚 微信 WeChat  - 规划中
echo   📷 Instagram    - 规划中
echo   🐦 Twitter/X    - 规划中
echo   💜 Discord      - 规划中
echo.
echo 提示：
echo - 按 Ctrl+C 可停止服务
echo - 不要关闭此窗口
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

REM Check and Install Dependencies
echo 🔍 正在检查依赖环境...
"%PYTHON_EXE%" -c "import PyPDF2, docx, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo 📦 检测到缺失依赖 (PyPDF2/docx/openpyxl)，正在自动安装...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请检查网络或手动运行 install.bat
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
)

REM Run Application
"%PYTHON_EXE%" -m streamlit run admin_multi.py

pause
