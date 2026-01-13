@echo off
setlocal EnableExtensions
chcp 65001 >nul

REM Fix for Python 3.14 + Protobuf compatibility (Must be set before any python call)
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

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
  set "USE_VENV=1"
) else if exist ".\venv313\Scripts\python.exe" (
  set "PYTHON_EXE=.\venv313\Scripts\python.exe"
  set "USE_VENV=1"
) else (
  set "PYTHON_EXE=python"
  set "USE_VENV=0"
)

REM Check Python version if using system Python
if "%USE_VENV%"=="0" (
  echo Checking Python version...
  "%PYTHON_EXE%" --version 2>nul | findstr /R "3\.14" >nul
  if not errorlevel 1 (
    echo.
    echo ================================================================
    echo   ERROR: Python 3.14 has compatibility issues with protobuf
    echo ================================================================
    echo.
    echo Detected Python 3.14, which is incompatible with protobuf/streamlit.
    echo.
    echo Solutions:
    echo   1. Create Python 3.13 virtual environment (Recommended)
    echo      install_runtime.bat
    echo.
    echo   2. Or install Python 3.13 and create virtual environment manually
    echo      py -3.13 -m venv venv313
    echo      venv313\Scripts\pip install -r requirements.txt
    echo.
    echo For details, see: USER_GUIDE.txt
    echo ================================================================
    echo.
    pause
    exit /b 1
  )
)

REM Check and Install Dependencies
echo Checking dependencies...
"%PYTHON_EXE%" -c "import streamlit, pypdf, docx, openpyxl, telethon, watchdog" >nul 2>&1
if errorlevel 1 (
    echo Missing deps detected: streamlit pypdf docx openpyxl telethon watchdog. Installing...
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
