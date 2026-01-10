#!/bin/bash

echo "================================================================"
echo "   🌐 AI Social Bot - 多平台管理中心"
echo "================================================================"
echo ""
echo "正在启动多平台管理后台..."
echo "浏览器将自动打开：http://localhost:8501"
echo ""
echo "支持的平台："
echo "  📱 Telegram     - 完整功能"
echo "  💬 WhatsApp     - 开发中"
echo "  📘 Facebook     - 规划中"
echo "  💙 Messenger    - 规划中"
echo "  💚 微信 WeChat  - 规划中"
echo "  📷 Instagram    - 规划中"
echo "  🐦 Twitter/X    - 规划中"
echo "  💜 Discord      - 规划中"
echo ""
echo "提示："
echo "- 按 Ctrl+C 可停止服务"
echo "- 不要关闭此终端"
echo "================================================================"
echo ""

streamlit run admin_multi.py


