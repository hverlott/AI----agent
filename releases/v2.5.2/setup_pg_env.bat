@echo off
echo ==========================================
echo SaaS-AIs PostgreSQL Environment Setup
echo ==========================================

echo.
echo 1. Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo 2. Setting up PostgreSQL database...
echo Please ensure your PostgreSQL server is running locally on port 5432.
echo Default user: postgres, password: postgres
echo If you have different credentials, set DB_USER and DB_PASS environment variables before running this.
echo.
python setup_pg.py

echo.
echo Setup process finished.
pause
