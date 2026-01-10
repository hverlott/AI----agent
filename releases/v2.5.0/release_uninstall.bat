@echo off
chcp 65001 >nul
echo ================================================
echo    🗑️ AI Talk - 卸载清理
echo ================================================
echo.
echo 此操作将删除当前目录下的所有文件！
echo 路径：%~dp0
echo.
set /p CONFIRM=确认继续？(Y/N): 
if /I "%CONFIRM%" NEQ "Y" (
  echo 已取消
  exit /b 0
)
echo 正在删除...
cd /d "%~dp0"
del /f /q * >nul 2>&1
for /d %%D in (*) do rd /s /q "%%D"
echo ✅ 清理完成
exit /b 0

