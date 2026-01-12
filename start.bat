@echo off
set "SAAS_ROOT=%~dp0"
set "SAAS_DATA_DIR=%SAAS_ROOT%data"
set "LATEST_VERSION=v2.5.1"

echo Starting SaaS AI Bot System (Version %LATEST_VERSION%)...
echo Data Directory: %SAAS_DATA_DIR%

if not exist "%SAAS_ROOT%releases\%LATEST_VERSION%" (
    echo Error: Version %LATEST_VERSION% not found in releases folder.
    pause
    exit /b 1
)

cd /d "%SAAS_ROOT%releases\%LATEST_VERSION%"
if exist "start_multi_admin.bat" (
    call start_multi_admin.bat %*
) else (
    echo Error: start_multi_admin.bat not found in version folder.
    pause
    exit /b 1
)
