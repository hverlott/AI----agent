@echo off
chcp 65001 >nul
echo ================================================================
echo    🤖 Telegram AI Bot - 一键安装脚本 (Windows)
echo ================================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未检测到 Python
    echo.
    echo 请先安装 Python 3.8 或更高版本:
    echo https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version
echo.

REM 检查 pip 是否可用
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：pip 不可用
    pause
    exit /b 1
)

echo ✅ pip 已安装
pip --version
echo.

echo ----------------------------------------------------------------
echo    步骤 1/4: 升级 pip
echo ----------------------------------------------------------------
python -m pip install --upgrade pip
echo.

echo ----------------------------------------------------------------
echo    步骤 2/4: 安装依赖包
echo ----------------------------------------------------------------
echo 正在安装 requirements.txt 中的包...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ❌ 依赖包安装失败
    echo.
    echo 💡 尝试手动安装：
    echo    pip install telethon openai python-dotenv httpx streamlit psutil
    pause
    exit /b 1
)
echo.

echo ----------------------------------------------------------------
echo    步骤 3/4: 创建配置文件
echo ----------------------------------------------------------------

REM 检查 .env 文件
if exist .env (
    echo ✅ .env 文件已存在，跳过创建
) else (
    if exist .env.example (
        echo 📝 从模板创建 .env 文件...
        copy .env.example .env >nul
        echo ✅ .env 文件已创建
    ) else (
        echo ⚠️ 警告：.env.example 不存在，需要手动创建 .env
    )
)

REM 检查 prompt.txt
if not exist prompt.txt (
    echo 📝 创建默认 prompt.txt...
    echo 你是一个幽默、专业的个人助理，帮机主回复消息。请用自然、友好的语气回复。 > prompt.txt
    echo ✅ prompt.txt 已创建
)

REM 检查 keywords.txt
if not exist keywords.txt (
    echo 📝 创建默认 keywords.txt...
    (
        echo 帮我
        echo 求助
        echo AI
        echo 机器人
    ) > keywords.txt
    echo ✅ keywords.txt 已创建
)
echo.

echo ----------------------------------------------------------------
echo    步骤 4/4: 运行环境检查
echo ----------------------------------------------------------------
python check_env.py
echo.

echo ================================================================
echo    ✅ 安装完成！
echo ================================================================
echo.
echo 📝 下一步操作：
echo.
echo    1. 编辑 .env 文件，填写你的 API 密钥：
echo       notepad .env
echo.
echo    2. 首次登录 Telegram：
echo       python main.py
echo.
echo    3. 启动管理后台：
echo       start_admin.bat
echo       或: streamlit run admin.py
echo.
echo ================================================================
pause


