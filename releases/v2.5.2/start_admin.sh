#!/bin/bash

echo "================================================"
echo "   🤖 Telegram AI Bot - 管理后台启动器"
echo "================================================"
echo ""
echo "正在启动 Web 管理界面..."
echo "浏览器将自动打开：http://localhost:8501"
echo ""
echo "提示："
echo "- 按 Ctrl+C 可停止服务"
echo "- 不要关闭此终端"
echo "================================================"
echo ""

streamlit run admin_multi.py


