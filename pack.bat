@echo off
echo ================================================================
echo    Telegram AI Bot - Packaging
echo ================================================================
python pack.py
if errorlevel 1 (
    echo.
    echo Python execution failed. Please ensure Python is installed.
    echo.
)
pause
