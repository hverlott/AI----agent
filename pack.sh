#!/bin/bash

echo "================================================================"
echo "   📦 Telegram AI Bot - 项目打包工具"
echo "================================================================"
echo ""
echo "正在打包项目文件..."
echo ""

# 设置打包文件名（带日期）
DATE=$(date +%Y%m%d)
PACKAGE_NAME="AI-Talk-Package-${DATE}.tar.gz"

echo "📝 打包文件列表："
echo "   ✓ 核心程序 (*.py)"
echo "   ✓ 配置文件 (*.txt, .env.example)"
echo "   ✓ 启动脚本 (*.bat, *.sh)"
echo "   ✓ 文档文件 (*.md)"
echo ""
echo "❌ 排除文件："
echo "   ✗ .env"
echo "   ✗ *.session"
echo "   ✗ bot.pid"
echo "   ✗ bot.log"
echo "   ✗ __pycache__"
echo ""

# 创建临时目录
TEMP_DIR="AI-Talk-Package"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# 复制文件
echo "正在复制文件..."
cp *.py "$TEMP_DIR/" 2>/dev/null
cp requirements.txt "$TEMP_DIR/" 2>/dev/null
cp prompt.txt "$TEMP_DIR/" 2>/dev/null
cp keywords.txt "$TEMP_DIR/" 2>/dev/null
cp config.txt "$TEMP_DIR/" 2>/dev/null
cp *.bat "$TEMP_DIR/" 2>/dev/null
cp *.sh "$TEMP_DIR/" 2>/dev/null
cp *.md "$TEMP_DIR/" 2>/dev/null
cp .env.example "$TEMP_DIR/" 2>/dev/null

# 创建压缩文件
echo "正在压缩..."
tar -czf "$PACKAGE_NAME" "$TEMP_DIR"

# 清理临时目录
rm -rf "$TEMP_DIR"

# 获取文件大小
SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)

echo ""
echo "================================================================"
echo "   ✅ 打包完成！"
echo "================================================================"
echo ""
echo "📦 文件名: $PACKAGE_NAME"
echo "📊 大小: $SIZE"
echo "📍 位置: $(pwd)/$PACKAGE_NAME"
echo ""
echo "💡 提示："
echo "   - 此压缩包不包含敏感文件 (.env, *.session)"
echo "   - 可以安全地分享或部署到新电脑"
echo "   - 解压后运行 ./install.sh 自动安装"
echo ""
echo "================================================================"

