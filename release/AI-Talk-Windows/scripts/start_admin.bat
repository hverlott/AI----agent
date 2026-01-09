@echo off
chcp 65001 >nul
echo ================================================
echo    🤖 Telegram AI Bot - 管理后台启动器
echo ================================================
echo.
echo 正在启动 Web 管理界面...
echo 浏览器将自动打开：http://localhost:8501
echo.
echo 提示：
echo - 按 Ctrl+C 可停止服务
echo - 不要关闭此窗口
echo ================================================
echo.

if exist ".\.venv313\Scripts\python.exe" (
  .\.venv313\Scripts\python -m streamlit run admin.py
) else (
  streamlit run admin.py
)

pause


