#!/bin/bash

echo "================================================================"
echo "   💬 WhatsApp AI Bot - 环境安装"
echo "================================================================"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误：未检测到 Node.js"
    echo ""
    echo "请先安装 Node.js 16+ 或更高版本:"
    echo "https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js 已安装"
node --version
echo ""

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误：npm 不可用"
    exit 1
fi

echo "✅ npm 已安装"
npm --version
echo ""

echo "----------------------------------------------------------------"
echo "   正在安装依赖包..."
echo "----------------------------------------------------------------"
npm install

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 依赖包安装失败"
    exit 1
fi

echo ""
echo "================================================================"
echo "   ✅ 安装完成！"
echo "================================================================"
echo ""
echo "📝 下一步操作："
echo ""
echo "   1. 确保已配置 .env 文件（项目根目录）"
echo ""
echo "   2. 启动机器人："
echo "      node bot.js"
echo ""
echo "   3. 使用 WhatsApp 扫描二维码登录"
echo ""
echo "================================================================"


