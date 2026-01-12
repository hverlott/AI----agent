@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo    AI Talk - Windows 打包脚本
echo ================================================================
echo.

REM 1) 创建/使用 Python 3.13 虚拟环境 venv313
set VENV_DIR=venv313
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo 🔧 正在创建 Python 3.13 虚拟环境: %VENV_DIR%
  py -3.13 -m venv %VENV_DIR%
)
set PY="%VENV_DIR%\Scripts\python.exe"
set PIP="%VENV_DIR%\Scripts\pip.exe"

echo ✅ 使用虚拟环境: %PY%
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
%PY% -m pip install pyinstaller
echo.

REM 2) 敏感信息排查（仅提示，不复制敏感文件）
echo ----------------------------------------------------------------
echo    步骤 2/5: 敏感信息检查
echo ----------------------------------------------------------------
if exist ".env" (
  echo ⚠️ 检测到 .env 文件，打包时将不会包含
)
for %%F in (*.session) do (
  echo ⚠️ 检测到 Session 文件: %%F，打包时将不会包含
)
echo ✅ 配置将仅包含 .env.example 与说明文档
echo.

REM 3) 使用 PyInstaller 生成可执行文件（控制台程序）
echo ----------------------------------------------------------------
echo    步骤 3/5: 生成可执行文件
echo ----------------------------------------------------------------
set DIST_BASE=dist
set BUILD_BASE=build
if exist "%DIST_BASE%" rd /s /q "%DIST_BASE%"
if exist "%BUILD_BASE%" rd /s /q "%BUILD_BASE%"

%PY% -m PyInstaller --clean --noconfirm --onefile --name AI_Talk_Bot main.py
if errorlevel 1 goto :pyi_error
%PY% -m PyInstaller --clean --noconfirm --onefile --name Broadcast_Tool broadcast.py
if errorlevel 1 goto :pyi_error
%PY% -m PyInstaller --clean --noconfirm --onefile --name Env_Check check_env.py
if errorlevel 1 goto :pyi_error
echo ✅ 可执行文件构建完成
echo.

REM 4) 组装发布目录
echo ----------------------------------------------------------------
echo    步骤 4/5: 组装发布目录
echo ----------------------------------------------------------------
set REL_DIR=release\\AI-Talk-Windows
if exist "release" rd /s /q "release"
mkdir "%REL_DIR%"
mkdir "%REL_DIR%\\bin"
mkdir "%REL_DIR%\\scripts"
mkdir "%REL_DIR%\\docs"

REM 复制可执行文件
copy /y "%DIST_BASE%\\AI_Talk_Bot.exe" "%REL_DIR%\\bin\\"
copy /y "%DIST_BASE%\\Broadcast_Tool.exe" "%REL_DIR%\\bin\\"
copy /y "%DIST_BASE%\\Env_Check.exe" "%REL_DIR%\\bin\\"

REM 复制依赖清单与安全配置样例
copy /y "requirements.txt" "%REL_DIR%\\"
if exist ".env.example" copy /y ".env.example" "%REL_DIR%\\"

REM 复制启动脚本（使用 venv313 运行 Streamlit 后台）
copy /y "start_admin.bat" "%REL_DIR%\\scripts\\"
copy /y "start_multi_admin.bat" "%REL_DIR%\\scripts\\"

REM 复制说明文档
copy /y "README.md" "%REL_DIR%\\docs\\"
copy /y "INSTALLATION.md" "%REL_DIR%\\docs\\"
copy /y "ADMIN_README.md" "%REL_DIR%\\docs\\"
copy /y "LOG_TROUBLESHOOTING.md" "%REL_DIR%\\docs\\"
copy /y "DEPLOYMENT_GUIDE.md" "%REL_DIR%\\docs\\"
copy /y "USER_GUIDE.txt" "%REL_DIR%\\docs\\"

REM 复制卸载脚本模板
copy /y "release_uninstall.bat" "%REL_DIR%\\uninstall.bat"

echo ✅ 发布目录已生成：%REL_DIR%
echo.

REM 5) 打包为 ZIP
echo ----------------------------------------------------------------
echo    步骤 5/5: 压缩为 ZIP
echo ----------------------------------------------------------------
powershell -NoProfile -Command "Compress-Archive -Path '%REL_DIR%\\*' -DestinationPath 'release\\AI-Talk-Windows.zip' -Force"
if errorlevel 1 (
  echo ❌ 压缩失败，请手动检查 release 目录
  goto :done
)
echo ✅ 压缩完成：release\\AI-Talk-Windows.zip
echo.

echo ================================================================
echo    打包完成
echo    - 可执行文件：release\\AI-Talk-Windows\\bin
echo    - 启动脚本：release\\AI-Talk-Windows\\scripts
echo    - 文档：release\\AI-Talk-Windows\\docs
echo    - 压缩包：release\\AI-Talk-Windows.zip
echo ================================================================
goto :done

:pyi_error
echo ❌ PyInstaller 构建失败
exit /b 1

:done
endlocal
