@echo off
setlocal EnableExtensions
chcp 65001 >nul
echo ================================================================
echo    AI Social Bot - Multi-Platform Admin Center
echo ================================================================
echo.
echo Starting admin console...
echo Browser will open: http://localhost:8501
echo.
echo Platforms:
echo   Telegram  - Full
echo   WhatsApp  - In progress
echo   Facebook  - Planned
echo   Messenger - Planned
echo   WeChat    - Planned
echo   Instagram - Planned
echo   Twitter/X - Planned
echo   Discord   - Planned
echo.
echo Tips:
echo - Press Ctrl+C to stop
echo - Keep this window open
echo ================================================================
echo.

REM Optional: only run checks, do not start Streamlit
set "ONLY_CHECK=0"
if /I "%~1"=="--check" set "ONLY_CHECK=1"

REM Select Python Interpreter
if exist ".\.venv313\Scripts\python.exe" (
  set "PYTHON_EXE=.\.venv313\Scripts\python.exe"
) else if exist ".\venv313\Scripts\python.exe" (
  set "PYTHON_EXE=.\venv313\Scripts\python.exe"
) else (
  set "PYTHON_EXE=python"
)

REM Check and Install Dependencies
echo Checking dependencies...
"%PYTHON_EXE%" -c "import streamlit, PyPDF2, docx, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo Missing deps detected: streamlit PyPDF2 docx openpyxl. Installing...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency install failed. Please check network or run install.bat
        pause
        exit /b 1
    )
    echo Dependencies installed.
)

if "%ONLY_CHECK%"=="1" (
  echo Check OK. Exiting due to --check.
  exit /b 0
)

REM Run Application
"%PYTHON_EXE%" -m streamlit run admin_multi.py

pause
