#!/bin/bash

echo "================================================================"
echo "   🤖 Telegram AI Bot - 一键安装脚本 (Linux/Mac)"
echo "================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误：未检测到 Python3${NC}"
    echo ""
    echo "请先安装 Python 3.8 或更高版本："
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Mac: brew install python@3.8"
    exit 1
fi

echo -e "${GREEN}✅ Python 已安装${NC}"
python3 --version
echo ""

# 检查 pip 是否可用
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ 错误：pip3 不可用${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pip 已安装${NC}"
pip3 --version
echo ""

echo "----------------------------------------------------------------"
echo "   步骤 1/4: 升级 pip"
echo "----------------------------------------------------------------"
python3 -m pip install --upgrade pip
echo ""

echo "----------------------------------------------------------------"
echo "   步骤 2/4: 安装依赖包"
echo "----------------------------------------------------------------"
echo "正在安装 requirements.txt 中的包..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ 依赖包安装失败${NC}"
    echo ""
    echo "💡 尝试手动安装："
    echo "   pip3 install telethon openai python-dotenv httpx streamlit psutil"
    exit 1
fi
echo ""

echo "----------------------------------------------------------------"
echo "   步骤 3/4: 创建配置文件"
echo "----------------------------------------------------------------"

# 检查 .env 文件
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env 文件已存在，跳过创建${NC}"
else
    if [ -f ".env.example" ]; then
        echo "📝 从模板创建 .env 文件..."
        cp .env.example .env
        echo -e "${GREEN}✅ .env 文件已创建${NC}"
    else
        echo -e "${YELLOW}⚠️ 警告：.env.example 不存在，需要手动创建 .env${NC}"
    fi
fi

# 检查 prompt.txt
if [ ! -f "prompt.txt" ]; then
    echo "📝 创建默认 prompt.txt..."
    echo "你是一个幽默、专业的个人助理，帮机主回复消息。请用自然、友好的语气回复。" > prompt.txt
    echo -e "${GREEN}✅ prompt.txt 已创建${NC}"
fi

# 检查 keywords.txt
if [ ! -f "keywords.txt" ]; then
    echo "📝 创建默认 keywords.txt..."
    cat > keywords.txt << EOF
帮我
求助
AI
机器人
EOF
    echo -e "${GREEN}✅ keywords.txt 已创建${NC}"
fi
echo ""

echo "----------------------------------------------------------------"
echo "   步骤 4/4: 运行环境检查"
echo "----------------------------------------------------------------"
python3 check_env.py
echo ""

echo "================================================================"
echo "   ✅ 安装完成！"
echo "================================================================"
echo ""
echo "📝 下一步操作："
echo ""
echo "   1. 编辑 .env 文件，填写你的 API 密钥："
echo "      nano .env"
echo "      或: vim .env"
echo ""
echo "   2. 首次登录 Telegram："
echo "      python3 main.py"
echo ""
echo "   3. 启动管理后台："
echo "      ./start_admin.sh"
echo "      或: streamlit run admin.py"
echo ""
echo "================================================================"


