#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多平台社交媒体 AI Bot - 统一管理后台
支持 Telegram, WhatsApp, Facebook, Messenger, 微信等
"""

import streamlit as st
import os
import sys
import json
import asyncio
import shutil
import pytz
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from business_core import BusinessCore
from database import db
from auth_core import AuthManager

import pandas as pd
from src.modules.telegram.utils import get_session_user
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

# 页面配置
st.set_page_config(
    page_title="👑鼎盛👑内部工具",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_VERSION = "2.3.0"

# CSS 样式（优化紧凑版）
st.markdown("""
<style>
    :root {
        --bg: #f6f3ec;
        --panel: #ffffff;
        --text: #1f2328;
        --muted: #5b6670;
        --accent: #0f6b6d;
        --accent-2: #d97706;
        --border: #e6dfd6;
        --shadow: 0 10px 30px rgba(15, 23, 42, 0.10);
    }
    .stApp {
        background:
            radial-gradient(1200px 520px at 10% -10%, #fff1d9 0%, transparent 60%),
            radial-gradient(900px 520px at 90% 0%, #e3f0ff 0%, transparent 55%),
            var(--bg);
        color: var(--text);
        font-family: "Segoe UI", "Microsoft YaHei", "Noto Sans SC", sans-serif;
    }
    [data-testid="stSidebar"] {
        background: #fbfaf7;
        border-right: 1px solid var(--border);
        padding-top: 1.6rem;
    }
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.35rem;
    }
    .block-container {
        padding-top: 1.4rem;
        max-width: 1200px;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        color: #0f6b6d;
        margin-bottom: 1.2rem;
    }
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.1rem 1.4rem;
        border-radius: 16px;
        background: linear-gradient(120deg, #0f6b6d, #134e4a);
        color: #f8f5ef;
        box-shadow: var(--shadow);
        margin-bottom: 1.2rem;
    }
    .topbar-title {
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: 0.4px;
    }
    .topbar-sub {
        font-size: 0.95rem;
        opacity: 0.85;
        margin-top: 0.2rem;
    }
    .topbar-meta .tag {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, 0.35);
        background: rgba(255, 255, 255, 0.15);
        font-size: 0.78rem;
        margin-left: 0.35rem;
    }
    .platform-card {
        padding: 0.9rem 1rem;
        border-radius: 12px;
        border: 1px solid var(--border);
        margin: 0.4rem 0;
        background: #ffffff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
        transition: all 0.2s ease;
    }
    .platform-card:hover {
        border-color: rgba(15, 107, 109, 0.35);
        box-shadow: 0 10px 18px rgba(15, 23, 42, 0.12);
    }
    .platform-active {
        border-color: rgba(15, 107, 109, 0.45) !important;
        background-color: #f2fbfb;
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-running {
        background-color: #d4edda;
        color: #155724;
    }
    .status-stopped {
        background-color: #f8d7da;
        color: #721c24;
    }
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 2.8rem;
        font-weight: 600;
        border: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 18px rgba(15, 23, 42, 0.12);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: #f5f1ea;
        border-radius: 999px;
        padding: 0.35rem 1rem;
        border: 1px solid var(--border);
    }
    .stTabs [aria-selected="true"] {
        background: #0f6b6d;
        color: #ffffff;
    }
    [data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.75rem 1rem;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    }
    [data-testid="stMetric"] label {
        color: var(--muted);
    }
    .stTextArea textarea,
    .stTextInput input {
        border-radius: 12px;
        border: 1px solid var(--border);
        background: #ffffff;
    }
    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: rgba(15, 107, 109, 0.45);
        box-shadow: 0 0 0 3px rgba(15, 107, 109, 0.15);
    }
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px;
    }
    .stSelectbox div[data-baseweb="select"] div[role="button"] {
        border: 1px solid var(--border);
        background: #ffffff;
    }
    details > summary {
        border-radius: 12px;
        background: #f8f5ef;
        border: 1px solid var(--border);
        padding: 0.4rem 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# 简易多语言与RBAC
LANGS = {
    "zh": "中文",
    "en": "English"
}
I18N = {
    "zh": {
        "nav_platform": "平台",
        "nav_role": "身份切换",
        "nav_lang": "语言",
        "nav_timezone": "时区",
        "nav_tenant": "租户",
        "nav_sys_info": "系统信息",
        "nav_help": "帮助",
        "nav_docs_arch": "系统架构文档",
        "nav_docs_kb": "知识库用户手册",
        
        "plat_knowledge": "知识库",
        "plat_knowledge_desc": "知识库配置与检索",
        "plat_audit": "审核配置",
        "plat_audit_desc": "关键词与日志管理",
        "plat_business": "商业化运营",
        "plat_business_desc": "订阅/计费/数据看板",
        "plat_telegram": "Telegram",
        "plat_telegram_desc": "全功能支持 - 私聊/群聊/频道",
        "plat_whatsapp": "WhatsApp",
        "plat_whatsapp_desc": "可用 - 私聊/群聊自动回复",
        "plat_accounts": "账号管理",
        "plat_accounts_desc": "集中录入与分组/标签管理",
        "plat_ai_config": "AGNT AI配置中心",
        "plat_ai_config_desc": "AI服务商接入与A/B测试",
        "plat_api_gateway": "API接口管理中心",
        "plat_api_gateway_desc": "统一网关/权限/流控/日志",
        "plat_sys_config": "系统配置自动化",
        "plat_sys_config_desc": "环境/会话/密钥自动化",
        
        "bus_header": "商业化运营中心",
        "bus_tab_dashboard": "数据看板",
        "bus_tab_sub": "订阅管理",
        "bus_tab_brand": "品牌定制",
        "bus_metrics_core": "核心指标",
        "bus_active_users": "今日活跃用户",
        "bus_api_calls": "API调用量",
        "bus_funnel": "转化漏斗",
        "bus_revenue": "本月预估营收",
        "bus_total_tokens": "总 Token 消耗",
        "bus_total_cost": "总成本估算 ($)",
        "bus_cost_breakdown": "成本分布 (按 Stage)",
        "bus_trend": "趋势分析",
        "bus_sub_plan": "订阅方案",
        "bus_current_plan": "当前方案",
        "bus_expiry": "到期时间",
        "bus_brand_title": "品牌定制 (White Label)",
        "bus_brand_warn": "此功能仅限 Pro/Enterprise 用户使用",
        "bus_company_name": "公司名称",
        "bus_theme_color": "主题色",
        "bus_save_brand": "保存品牌设置",
        "bus_save_success": "设置已保存",
        
        "bus_plan_free_title": "免费版 (Free)",
        "bus_plan_free_feat1": "- 1 个机器人实例",
        "bus_plan_free_feat2": "- 每日 100 条消息",
        "bus_plan_free_btn": "降级/选择",
        
        "bus_plan_pro_title": "专业版 ($99/月)",
        "bus_plan_pro_feat1": "- 5 个机器人实例",
        "bus_plan_pro_feat2": "- 每日 5,000 条消息",
        "bus_plan_pro_feat3": "- 数据分析看板",
        "bus_plan_pro_btn": "升级到专业版",
        
        "bus_plan_ent_title": "企业版 ($999/月)",
        "bus_plan_ent_feat1": "- 无限机器人",
        "bus_plan_ent_feat2": "- 品牌定制 (White Label)",
        "bus_plan_ent_feat3": "- 专属技术支持",
        "bus_plan_ent_btn": "联系销售",
        
        "common_select": "选择",
        "common_selected": "✓",
        "common_save": "保存",
        "common_success": "成功",
        "common_error": "错误",
        "common_edit": "编辑",
        "common_delete": "删除",
        "common_cancel": "取消",
        "common_confirm": "确认",
        "common_back": "返回",
        "common_next": "下一步",
        "common_finish": "完成",

        "kb_header": "知识库配置与管理",
        "kb_tab_manage": "管理",
        "kb_tab_import": "导入",
        "kb_tab_test": "检索测试",
        "kb_tab_settings": "设置",
        "kb_list_title": "知识条目列表",
        "kb_no_items": "暂无条目，可在“导入”或下方创建。",
        "kb_col_title": "标题",
        "kb_col_category": "分类",
        "kb_col_tags": "标签",
        "kb_col_source": "来源文件",
        "kb_col_action": "操作",
        "kb_new_item": "新建文本条目",
        "kb_input_title": "标题",
        "kb_input_cat": "分类",
        "kb_input_tags": "标签（逗号分隔）",
        "kb_input_content": "内容",
        "kb_btn_save": "保存条目",
        "kb_err_empty": "请输入标题或内容",
        "kb_edit_title": "编辑条目",
        "kb_import_header": "导入文件",
        "kb_import_desc": "选择文件（支持 txt/md/pdf/docx/xlsx）",
        "kb_import_preview": "内容预览（可编辑）",
        "kb_import_save": "保存为条目",
        "kb_test_header": "检索测试",
        "kb_test_input": "输入检索关键词或问题",
        "kb_test_topn": "返回条数",
        "kb_test_btn": "执行检索",
        "kb_settings_header": "设置与依赖",

        "tg_header": "Telegram AI Bot 控制面板",
        "tg_status_running": "🟢 运行中",
        "tg_status_stopped": "🔴 已停止",
        "tg_status_logged_in": "✅ 已登录",
        "tg_status_not_logged_in": "⚠️ 未登录",
        "tg_btn_login": "未登录 Telegram（点击登录）",

        "tg_tab_config": "🧠 配置",
        "tg_tab_broadcast": "📢 群发",
        "tg_tab_logs": "📜 日志",
        "tg_tab_stats": "📊 统计",
        "tg_tab_flow": "🧭 时序图",

        "tg_config_header": "⚙️ 配置管理",
        "tg_cfg_persona": "**AI 人设**",
        "tg_cfg_prompt_label": "编辑提示词",
        "tg_cfg_save_prompt": "💾 保存人设",
        "tg_cfg_keywords": "**触发关键词**",
        "tg_cfg_keywords_placeholder": "每行一个",
        "tg_cfg_save_keywords": "💾 保存关键词",
        "tg_cfg_qa": "**QA问题库**",
        "tg_cfg_qa_placeholder": "QA问题库（支持 Q:/A: 或 question||answer）",
        "tg_cfg_save_qa": "💾 保存QA",
        "tg_cfg_switches": "**功能开关**",
        "tg_cfg_private_reply": "私聊自动回复",
        "tg_cfg_group_reply": "群聊自动回复",
        "tg_cfg_quote": "**引用设置**",
        "tg_cfg_auto_quote": "自动引用",
        "tg_cfg_quote_interval": "引用时间间隔(秒)",
        "tg_cfg_quote_len": "引用内容长度(字符)",
        "tg_cfg_temp": "**🌡️ AI 创造性 (Temperature)**",
        "tg_cfg_temp_label": "调整 AI 回复的随机性与创造性",
        "tg_cfg_audit": "**🛡️ 内容审核系统 (双机拦截)**",
        "tg_cfg_audit_enable": "启用审核员 AI",
        "tg_cfg_audit_mode": "审核模式",
        "tg_cfg_audit_retries": "最大重试次数",
        "tg_cfg_audit_strictness": "审核员严格度",
        "tg_cfg_audit_guide": "合规引导强度",
        "tg_cfg_audit_temp_off": "⏸️ 临时关闭审核（5分钟）",
        "tg_cfg_audit_restore": "▶️ 立即恢复审核配置",
        "tg_cfg_audit_servers": "远程审核服务器地址 (多个用逗号分隔)",
        "tg_cfg_save_all": "💾 保存配置",
        "tg_cfg_audit_kw": "**🔒 审核员关键词配置（双机拦截）**",
        "tg_cfg_conv_mode": "对话呈现模式",
        "tg_cfg_conv_ai": "官方客服 / 技术支持",
        "tg_cfg_conv_human": "模拟真人沟通",
        "tg_kw_block": "违禁词",
        "tg_kw_sensitive": "敏感词",
        "tg_kw_allow": "允许词（品牌设定白名单）",
        "tg_kw_add": "添加",
        "tg_kw_del": "删除选中",
        "tg_kw_rename": "重命名",
        "tg_kw_new_name": "新名称",
        "tg_kw_fallback": "**📝 审核员兜底话术库（每行一条）**",
        "tg_kw_save_fallback": "💾 保存兜底话术",
        "tg_kw_clean_qa": "**🧹 QA 知识库清理**",
        "tg_kw_clean_btn": "🔎 扫描并清理不合规条目",
        "tg_whitelist_header": "📌 群白名单",
        "tg_whitelist_select": "选择允许自动回复的群组",
        "tg_whitelist_save": "💾 保存白名单",

        "tg_bc_header": "📢 群发",
        "tg_bc_warn": "⚠️ 频繁群发可能导致账号被限制，建议小批量测试。",
        "tg_bc_mode": "群组加载方式",
        "tg_bc_mode_whitelist": "白名单群组",
        "tg_bc_mode_non_whitelist": "非白名单群组",
        "tg_bc_mode_all": "全部群组",
        "tg_bc_load_btn": "加载群组",
        "tg_bc_select_all": "全选",
        "tg_bc_select_none": "全不选",
        "tg_bc_select_invert": "反选",
        "tg_bc_select_label": "选择群组",
        "tg_bc_interval": "群发间隔（秒）",
        "tg_bc_msg_placeholder": "输入要群发的消息...",
        "tg_bc_send_btn": "🚀 开始群发",
        "tg_bc_records": "📋 群发记录",
        "tg_bc_clear": "清空记录",

        "tg_log_header": "📜 运行日志",
        "tg_log_sys": "系统日志",
        "tg_log_priv": "私聊日志",
        "tg_log_grp": "群聊日志",
        "tg_log_audit": "审核日志",
        "tg_log_load": "加载日志",
        "tg_log_refresh": "刷新",
        "tg_log_clear": "清空日志",

        "tg_flow_header": "🧭 客户到 AI 回复时序",
        "tg_btn_start": "🚀 启动机器人",
        "tg_btn_stop": "⛔ 停止机器人",
        "tg_btn_restart": "🔄 重启机器人",
        "tg_restart_success": "机器人已重启",
        "tg_login_header": "Telegram 登录",
        "tg_login_success": "✅ 已登录",
        "tg_login_warning": "⚠️ 未登录",
        "tg_login_btn": "未登录 Telegram（点击登录）",
        "tg_config_success": "✅ 已配置",
        "tg_config_missing": "❌ 未配置",
        "tg_panel_header": "📱 Telegram AI Bot 控制面板",
        "tg_flow_entry": "**入口**：用户在 Telegram 发送消息 → Telethon 捕获 NewMessage → main.py 统一处理",
        "tg_flow_trigger": "**触发检查**：私聊/被@/关键词/上下文/群白名单",
        "tg_flow_branch_a": "**分支 A：QA 命中**",
        "tg_flow_branch_a_1": "- 解析 qa.txt 匹配固定答案",
        "tg_flow_branch_a_2": "- 直接回复到 Telegram",
        "tg_flow_branch_a_3": "- 写入日志与更新统计",
        "tg_flow_branch_b": "**分支 B：QA 未命中**",
        "tg_flow_branch_b_1": "- 检索知识库 Top-2 作为上下文",
        "tg_flow_branch_b_2": "- 调用 AI 生成草稿",
        "tg_flow_branch_b_3": "- 关键词前置拦截：允许词优先；命中违禁/敏感→兜底",
        "tg_flow_branch_b_4": "- 审核员 AI（双机拦截）：本地/远程，返回 PASS/FAIL 与建议",
        "tg_flow_branch_b_5": "- FAIL 重试至上限，超限兜底；PASS 发送 AI 回复",
        "tg_flow_branch_b_6": "- 写入审核与系统日志，更新统计",
        "tg_flow_kw_prio": "**关键词优先级**",
        "tg_flow_kw_prio_1": "- allow：命中直接允许",
        "tg_flow_kw_prio_2": "- block：命中直接拒绝，触发兜底",
        "tg_flow_kw_prio_3": "- sensitive：记录并拒绝（可调整为警告）",
        "tg_flow_fallback": "**兜底话术**",
        "tg_flow_fallback_1": "- 来源：platforms/telegram/audit_fallback.txt",
        "tg_flow_fallback_2": "- 可在配置页直接编辑并保存",
        "tg_flow_files": "**文件与模块**",
        "tg_flow_files_1": "- 处理主链路：[main.py](file:///d:/AI%20Talk/main.py)",
        "tg_flow_files_2": "- 审核与兜底：[audit_manager.py](file:///d:/AI%20Talk/audit_manager.py)",
        "tg_flow_files_3": "- 关键词管理：[keyword_manager.py](file:///d:/AI%20Talk/keyword_manager.py)",
        "tg_flow_files_4": "- 配置后台：[admin_multi.py](file:///d:/AI%20Talk/admin_multi.py)",
        "tg_stats_total_users": "总用户数",
        "tg_stats_active_today": "今日活跃",
        "tg_stats_total_msgs": "总消息数",
        "tg_stats_trend_7d": "近7日趋势",
        "tg_stats_title": "使用统计",
        "tg_stats_total_replies": "总回复数",
        "tg_stats_success_rate": "成功率",
        "tg_stats_fail_count": "失败次数",
        "tg_stats_private": "私聊消息",
        "tg_stats_group": "群聊消息",
        "tg_stats_uptime_fmt": "⏱️ 运行时长: {d}天 {h}小时 {m}分钟",
        "tg_stats_last_active": "最后活跃: {}",
        "tg_stats_audit_trend": "审核与兜底趋势",
        "tg_stats_audit_desc": "统计最近 1000 行审核日志中的 PASS/FAIL/兜底触发次数",
        "tg_stats_chart_cat": "类别",
        "tg_stats_chart_count": "次数",
        "tg_stats_chart_fallback": "兜底",
        "tg_stats_reset": "🗑️ 重置统计",
        "tg_stats_reset_success": "✅ 统计已重置",
        "tg_stats_read_fail": "读取统计失败: {}",
        "tg_stats_tip_wait": "💡 统计数据将在机器人运行后生成",
        "wa_header": "WhatsApp 自动回复机器人",
        "wa_qr_title": "WhatsApp 登录二维码",
        "wa_qr_scan_hint": "请使用手机 WhatsApp 扫描下方二维码登录",
        "wa_qr_caption": "扫描此二维码登录",
        "wa_qr_step1": "提示：打开 WhatsApp > 设置 > 已连接的设备 > 连接设备",
        "wa_qr_step2": "⏳ 二维码有效期约 20 秒，过期请重启机器人",
        "wa_qr_refresh": "🔄 刷新查看状态",
        "wa_status_read_err": "读取登录状态失败: {}",
        "wa_btn_start": "🚀 启动机器人",
        "wa_btn_stop": "⛔ 停止机器人",
        "wa_btn_restart": "🔄 重启机器人",
        "wa_restart_success": "机器人已重启",
        "wa_log_header": "📜 运行日志",
        "wa_log_refresh": "🔄 刷新日志",
        "wa_log_empty": "📝 日志为空，等待机器人产生输出...",
        "wa_log_missing": "⚠️ 日志文件不存在，请先启动机器人",
        "wa_log_clear": "🗑️ 清空日志",
        "wa_log_cleared": "✅ 日志已清空",
        "wa_stats_header": "📊 使用统计",
        "wa_stats_reset": "🗑️ 重置统计",
        "wa_stats_reset_success": "✅ 统计已重置",
        "wa_cfg_header": "⚙️ 配置管理",
        "wa_cfg_persona": "AI 人设",
        "wa_cfg_prompt_label": "编辑提示词",
        "wa_cfg_save_prompt": "💾 保存人设",
        "wa_cfg_keywords": "触发关键词",
        "wa_cfg_keywords_label": "群聊关键词（每行一个）",
        "wa_cfg_save_keywords": "💾 保存关键词",
        "wa_cfg_switches": "功能开关",
        "wa_cfg_private_reply": "私聊回复",
        "wa_cfg_group_reply": "群聊回复",
        "wa_cfg_save_config": "💾 保存开关配置",
        "wa_cfg_tip_restart": "💡 修改后立即生效，无需重启机器人",
        "wa_log_file_size": "📁 文件大小: {} 字节",
        "wa_log_last_updated": "📅 最后更新: {}",
        "wa_log_read_err": "❌ 读取日志失败: {}",
        "wa_log_clear_fail": "❌ 清空失败",
        "wa_stats_total_msgs": "总消息数",
        "wa_stats_total_replies": "总回复数",
        "wa_stats_success_rate": "成功率",
        "wa_stats_failures": "失败次数",
        "wa_stats_private": "私聊消息",
        "wa_stats_group": "群聊消息",
        "wa_stats_runtime": "⏱️ 运行时长: {d}天 {h}小时 {m}分钟",
        "wa_stats_last_active": "最后活跃: {}",
        "wa_stats_read_err": "读取统计失败: {}",
        "wa_stats_wait": "💡 统计数据将在机器人运行后生成",
        
        "orch_header": "AI剧本配置 Orchestrator",
        "orch_tab_stage": "Stage 管理",
        "orch_tab_persona": "Persona 管理",
        "orch_tab_binding": "绑定关系",
        "orch_stage_name": "Stage 名称",
        "orch_stage_version": "版本",
        "orch_stage_content": "内容(JSON)",
        "orch_btn_save_stage": "保存 Stage",
        "orch_persona_name": "Persona 名称",
        "orch_persona_version": "版本",
        "orch_persona_content": "内容(JSON)",
        "orch_btn_save_persona": "保存 Persona",
        "orch_binding_content": "Stage×Persona→AgentProfile 映射(JSON)",
        "orch_btn_save_binding": "保存绑定",
        "orch_save_success": "✅ 已保存",
        "sup_header": "Supervisor 监控台",
        "sup_list_title": "当前会话列表",
        "sup_select_user": "选择会话",
        "sup_force_stage": "强制 Stage",
        "sup_force_persona": "强制 Persona",
        "sup_handoff": "人工接管",
        "sup_btn_apply": "应用",
        "sup_apply_success": "✅ 已应用",
        "sup_route_title": "最近路由决策",
        "sup_route_col_user": "用户",
        "sup_route_col_platform": "平台",
        "sup_route_col_time": "时间",
        "sup_route_col_decision": "决策",
        
        "common_coming_soon": "{} - 开发中",
        "common_in_dev": "### 🚧 平台开发中",
        "common_planned_features": "**计划功能：**",
        "common_contact_dev": "💡 如果你急需此平台支持，请联系开发者。",
        "common_dev_progress": "### 📈 开发进度",
        "common_progress_fmt": "完成度: {}%",
        
        "audit_header": "🛡️ 审核员配置中心",
        "audit_role_warn": "仅审核员可访问此模块。请在左侧切换身份为 Auditor。",
        "audit_tab_keywords": "关键词管理",
        "audit_tab_logs": "审核日志",
        "audit_tab_config": "配置",
        "audit_cfg_enable": "启用审核系统",
        "audit_cfg_remote": "使用远程审核服务",
        "audit_cfg_url": "远程服务地址",
        "audit_cfg_remote_help": "多个地址用逗号分隔，优先使用第一个",
        "audit_cfg_key": "API 密钥",
        "audit_cfg_save": "保存配置",
        "audit_log_col_time": "时间",
        "audit_log_col_role": "角色",
        "audit_log_col_action": "动作",
        "audit_log_col_details": "详情",
        "audit_log_no_data": "暂无日志",
        "audit_kw_info": "此处配置的关键词将实时生效，用于拦截或标记敏感内容。",
        "audit_block_header": "#### 🚫 违禁词 (Block)",
        "audit_block_caption": "触发此类关键词将直接拦截回复",
        "audit_block_count": "当前共 {} 个违禁词",
        "audit_block_add": "添加违禁词",
        "audit_block_add_btn": "添加",
        "audit_block_del_sel": "选择要删除的违禁词",
        "audit_block_del_btn": "删除选中",
        "audit_block_rename_sel": "选择重命名的违禁词",
        "audit_block_rename_new": "新的名称",
        "audit_block_rename_btn": "重命名",
        "audit_sens_header": "#### ⚠️ 敏感词 (Sensitive)",
        "audit_sens_caption": "触发此类关键词将记录日志并拒绝（或警告）",
        "audit_sens_count": "当前共 {} 个敏感词",
        "audit_sens_add": "添加敏感词",
        "audit_sens_del_sel": "选择要删除的敏感词",
        "audit_sens_rename_sel": "选择重命名的敏感词",
        "audit_allow_header": "#### ✅ 允许词（品牌设定白名单）",
        "audit_allow_count": "当前共 {} 个允许词",
        "audit_allow_add": "添加允许词",
        "audit_allow_del_sel": "选择要删除的允许词",
        "audit_allow_rename_sel": "选择重命名的允许词",
        "audit_log_recent": "最近审核日志",
        "audit_log_refresh": "刷新日志",
        
        "api_header": "API接口管理中心",
        "api_route_path": "接口路径 /audit /reply",
        "api_route_method": "方法",
        "api_route_auth": "鉴权",
        "api_route_rate": "流量限制 req/min",
        "api_btn_add": "添加/更新路由",
        "api_save_success": "✅ 已保存路由",
        "api_list_header": "路由列表",

        "sys_header": "系统配置自动化",
        "sys_env_header": "环境配置 (env)",
        "sys_status": "状态",
        "sys_status_gen": "已生成",
        "sys_status_not_gen": "未生成",
        "sys_file_path": "文件: {}",
        "sys_btn_gen_env": "一键生成/更新 .env",
        "sys_success_env": "✅ .env 已生成/更新",
        "sys_session_header": "会话文件生成",
        "sys_btn_init_session": "静默初始化会话文件",
        "sys_success_session": "✅ 会话文件已初始化",
        "sys_secret_header": "敏感信息加密与查看",
        "sys_secret_caption": "默认显示为掩码；查看需二次验证并记录审计日志",
        "sys_btn_gen_code": "生成二次验证码",
        "sys_code_info": "已生成，请输入验证码进行查看",
        "sys_input_code": "输入验证码以查看",
        "sys_btn_view": "查看明文",
        "sys_success_view": "✅ 验证通过（当前会话有效）",
        "sys_err_code": "验证码不正确",
        
        "acc_header": "账号管理",
        "acc_tenant": "当前租户: {}",
        "acc_subtitle": "平台/账号集中录入与分组、标签管理",
        "acc_col_platform": "平台",
        "acc_col_username": "账号名/ID",
        "acc_col_group": "分组",
        "acc_col_tags": "标签（逗号分隔）",
        "acc_col_refresh": "刷新间隔（分钟）",
        "acc_btn_add": "添加/更新账号",
        
        "cs_title": "🚧 平台开发中",
        "cs_desc": "**{}** 功能正在开发中，敬请期待！",
        "cs_plan_title": "**计划功能：**",
        "cs_plan_1": "✅ 自动回复",
        "cs_plan_2": "✅ 上下文记忆",
        "cs_plan_3": "✅ 群发消息",
        "cs_plan_4": "✅ Web 管理",
        "cs_plan_5": "✅ 统计报表",
        "cs_eta": "**预计上线：** 待定",
        "cs_contact": "💡 如果你急需此平台支持，请联系开发者。",
        "cs_progress_title": "### 📈 开发进度",
        "cs_progress_caption": "完成度: {}%",
        
        "wa_status_running": "🟢 运行中",
        "wa_status_stopped": "🔴 已停止",
        "wa_start_success": "✅ WhatsApp 机器人已启动 (PID: {})",
        "wa_start_fail": "❌ 启动失败: {}",
        "wa_err_no_node": "❌ 未检测到 Node.js，请先安装",
        "wa_err_missing_deps": "❌ 依赖缺失，请先运行 install.bat/ install.sh",
        "wa_stop_success": "✅ WhatsApp 机器人已停止",
        "wa_stop_not_running": "⚠️ 机器人未运行",
        "wa_stop_fail": "❌ 停止失败: {}",
        "audit_db_err": "无法从数据库加载日志: {}",
        "audit_save_err": "保存配置失败: {}",
        "acc_save_success": "✅ 已保存账号",
        "acc_list_title": "账号列表",
        "ai_subtitle": "可视化配置AI服务商、模型版本与A/B权重",
        "ai_provider": "服务商",
        "ai_base_url": "Base URL",
        "ai_model": "模型版本",
        "ai_weight": "A/B权重",
        "ai_api_key": "API Key（不落盘展示）",
        "ai_timeout": "请求超时（秒）",
        "tg_bc_logs_label": "日志",
        "tg_bc_exec_err": "执行错误: {}",
    },
    "en": {
        "nav_platform": "Platform",
        "nav_role": "Role Switch",
        "nav_lang": "Language",
        "nav_timezone": "Timezone",
        "nav_tenant": "Tenant",
        "nav_sys_info": "System Info",
        "nav_help": "Help",
        "nav_docs_arch": "System Architecture",
        "nav_docs_kb": "KB User Guide",
        
        "plat_knowledge": "Knowledge Base",
        "plat_knowledge_desc": "KB Config & Retrieval",
        "plat_audit": "Audit Config",
        "plat_audit_desc": "Keywords & Logs",
        "plat_business": "Business Ops",
        "plat_business_desc": "Sub/Billing/Dashboard",
        "plat_telegram": "Telegram",
        "plat_telegram_desc": "Full Support - DM/Group/Channel",
        "plat_whatsapp": "WhatsApp",
        "plat_whatsapp_desc": "Available - DM/Group Auto-reply",
        "plat_accounts": "Accounts",
        "plat_accounts_desc": "Centralized Accounts & Tags",
        "plat_ai_config": "AGNT AI Config",
        "plat_ai_config_desc": "AI Providers & A/B Testing",
        "plat_api_gateway": "API Gateway",
        "plat_api_gateway_desc": "Gateway/Auth/RateLimit/Logs",
        "plat_sys_config": "System Config",
        "plat_sys_config_desc": "Env/Session/Keys Auto",
        
        "bus_header": "Business Operations Center",
        "bus_tab_dashboard": "Dashboard",
        "bus_tab_sub": "Subscription",
        "bus_tab_brand": "Branding",
        "bus_metrics_core": "Core Metrics",
        "bus_active_users": "Active Users (Today)",
        "bus_api_calls": "API Calls",
        "bus_funnel": "Conversion Funnel",
        "bus_revenue": "Est. Revenue (Mo)",
        "bus_total_tokens": "Total Tokens",
        "bus_total_cost": "Total Cost ($)",
        "bus_cost_breakdown": "Cost Breakdown (by Stage)",
        "bus_trend": "Trend Analysis",
        "bus_sub_plan": "Subscription Plans",
        "bus_current_plan": "Current Plan",
        "bus_expiry": "Expires At",
        "bus_brand_title": "White Label Branding",
        "bus_brand_warn": "Feature available for Pro/Enterprise only",
        "bus_company_name": "Company Name",
        "bus_theme_color": "Theme Color",
        "bus_save_brand": "Save Branding",
        "bus_save_success": "Settings Saved",
        
        "bus_plan_free_title": "Free Plan",
        "bus_plan_free_feat1": "- 1 Bot Instance",
        "bus_plan_free_feat2": "- 100 Daily Msgs",
        "bus_plan_free_btn": "Downgrade/Select",
        
        "bus_plan_pro_title": "Pro Plan ($99/mo)",
        "bus_plan_pro_feat1": "- 5 Bot Instances",
        "bus_plan_pro_feat2": "- 5,000 Daily Msgs",
        "bus_plan_pro_feat3": "- Analytics Dashboard",
        "bus_plan_pro_btn": "Upgrade to Pro",
        
        "bus_plan_ent_title": "Enterprise ($999/mo)",
        "bus_plan_ent_feat1": "- Unlimited Bots",
        "bus_plan_ent_feat2": "- White Labeling",
        "bus_plan_ent_feat3": "- Dedicated Support",
        "bus_plan_ent_btn": "Contact Sales",
        
        "common_select": "Select",
        "common_selected": "✓",
        "common_save": "Save",
        "common_success": "Success",
        "common_error": "Error",
        "common_edit": "Edit",
        "common_delete": "Delete",
        "common_cancel": "Cancel",
        "common_confirm": "Confirm",
        "common_back": "Back",
        "common_next": "Next",
        "common_finish": "Finish",

        "kb_header": "Knowledge Base Management",
        "kb_tab_manage": "Manage",
        "kb_tab_import": "Import",
        "kb_tab_test": "Test",
        "kb_tab_settings": "Settings",
        "kb_list_title": "Knowledge Items",
        "kb_no_items": "No items found. Create below or Import.",
        "kb_col_title": "Title",
        "kb_col_category": "Category",
        "kb_col_tags": "Tags",
        "kb_col_source": "Source File",
        "kb_col_action": "Action",
        "kb_new_item": "New Text Item",
        "kb_input_title": "Title",
        "kb_input_cat": "Category",
        "kb_input_tags": "Tags (comma separated)",
        "kb_input_content": "Content",
        "kb_btn_save": "Save Item",
        "kb_err_empty": "Title or Content required",
        "kb_edit_title": "Edit Item",
        "kb_import_header": "Import Files",
        "kb_import_desc": "Upload Files (txt/md/pdf/docx/xlsx)",
        "kb_import_preview": "Content Preview (Editable)",
        "kb_import_save": "Save as Item",
        "kb_test_header": "Retrieval Test",
        "kb_test_input": "Enter keywords or question",
        "kb_test_topn": "Top N",
        "kb_test_btn": "Search",
        "kb_settings_header": "Settings & Dependencies",

        "tg_header": "Telegram AI Bot Control Panel",
        "tg_status_running": "🟢 Running",
        "tg_status_stopped": "🔴 Stopped",
        "tg_status_logged_in": "✅ Logged In",
        "tg_status_not_logged_in": "⚠️ Not Logged In",
        "tg_btn_login": "Login to Telegram",
        
        "tg_tab_config": "Config",
        "tg_tab_broadcast": "Broadcast",
        "tg_tab_logs": "Logs",
        "tg_tab_stats": "Stats",
        "tg_tab_flow": "Flow",

        "tg_config_header": "Config Management",
        "tg_cfg_persona": "AI Persona",
        "tg_cfg_prompt_label": "Edit Prompt",
        "tg_cfg_save_prompt": "Save Persona",
        "tg_cfg_keywords": "Keywords",
        "tg_cfg_keywords_placeholder": "One per line",
        "tg_cfg_save_keywords": "Save Keywords",
        "tg_cfg_qa": "QA Knowledge Base",
        "tg_cfg_qa_placeholder": "QA DB (Supports Q:/A: or question||answer)",
        "tg_cfg_save_qa": "Save QA",
        "tg_cfg_switches": "Feature Switches",
        "tg_cfg_private_reply": "Private Auto-Reply",
        "tg_cfg_group_reply": "Group Auto-Reply",
        "tg_cfg_quote": "Quote Settings",
        "tg_cfg_auto_quote": "Auto Quote",
        "tg_cfg_quote_interval": "Quote Interval (s)",
        "tg_cfg_quote_len": "Quote Max Length",
        "tg_cfg_temp": "AI Temperature",
        "tg_cfg_temp_label": "Adjust AI creativity/randomness",
        "tg_cfg_audit": "Content Audit System",
        "tg_cfg_audit_enable": "Enable Audit AI",
        "tg_cfg_audit_mode": "Audit Mode",
        "tg_cfg_audit_retries": "Max Retries",
        "tg_cfg_audit_strictness": "Audit Strictness",
        "tg_cfg_audit_guide": "Guide Strength",
        "tg_cfg_audit_temp_off": "Pause Audit (5min)",
        "tg_cfg_audit_restore": "Restore Audit Config",
        "tg_cfg_audit_servers": "Remote Audit Servers (comma separated)",
        "tg_cfg_save_all": "Save Config",
        "tg_cfg_audit_kw": "Auditor Keywords Config",
        "tg_cfg_conv_mode": "Conversation Mode",
        "tg_cfg_conv_ai": "AI Visible (Official Support)",
        "tg_cfg_conv_human": "Human Simulated",
        "tg_kw_block": "Blocklist",
        "tg_kw_sensitive": "Sensitive",
        "tg_kw_allow": "Allowlist",
        "tg_kw_add": "Add",
        "tg_kw_del": "Delete Selected",
        "tg_kw_rename": "Rename",
        "tg_kw_new_name": "New Name",
        "tg_kw_fallback": "Audit Fallback Responses",
        "tg_kw_save_fallback": "Save Fallback",
        "tg_kw_clean_qa": "Clean QA DB",
        "tg_kw_clean_btn": "Scan & Clean Invalid Items",
        "tg_whitelist_header": "Group Whitelist",
        "tg_whitelist_select": "Select Whitelisted Groups",
        "tg_whitelist_save": "Save Whitelist",

        "tg_bc_header": "Broadcast",
        "tg_bc_warn": "Warning: Frequent broadcasts may lead to account bans.",
        "tg_bc_mode": "Load Mode",
        "tg_bc_mode_whitelist": "Whitelist Only",
        "tg_bc_mode_non_whitelist": "Non-Whitelist Only",
        "tg_bc_mode_all": "All Groups",
        "tg_bc_load_btn": "Load Groups",
        "tg_bc_select_all": "Select All",
        "tg_bc_select_none": "Select None",
        "tg_bc_select_invert": "Invert Selection",
        "tg_bc_select_label": "Select Groups",
        "tg_bc_interval": "Interval (s)",
        "tg_bc_msg_placeholder": "Enter message...",
        "tg_bc_send_btn": "Start Broadcast",
        "tg_bc_records": "Broadcast Records",
        "tg_bc_clear": "Clear Records",
        "tg_broadcast_input_label": "Broadcast Message",
        "tg_bc_tip_load": "Please click Load Groups",

        "tg_log_header": "Runtime Logs",
        "tg_log_sys": "System Log",
        "tg_log_priv": "Private Log",
        "tg_log_grp": "Group Log",
        "tg_log_audit": "Audit Log",
        "tg_log_load": "Load Log",
        "tg_log_refresh": "Refresh",
        "tg_log_clear": "Clear Log",

        "tg_flow_header": "Customer to AI Flow",
        "tg_btn_start": "Start Bot",
        "tg_btn_stop": "Stop Bot",
        "tg_btn_restart": "Restart Bot",
        "tg_restart_success": "Bot Restarted",
        "tg_login_header": "Telegram Login",
        "tg_login_success": "Logged In",
        "tg_login_warning": "Not Logged In",
        "tg_login_btn": "Login to Telegram",
        "tg_config_success": "Configured",
        "tg_config_missing": "Not Configured",
        "tg_panel_header": "Telegram AI Bot Control Panel",
        "tg_broadcast_subtitle": "Send message to all active users",
        "tg_broadcast_success": "Simulated send: {}",
        "tg_logs_subtitle": "Showing last 50 records",
        "tg_stats_title": "Statistics",
        "tg_stats_total_users": "Total Users",
        "tg_stats_active_today": "Active Today",
        "tg_stats_total_msgs": "Total Messages",
        "tg_stats_trend_7d": "7-Day Trend",
        "tg_flow_subtitle": "System Message Processing Flow",
        "tg_flow_entry": "**Entry**: User sends message on Telegram → Telethon captures NewMessage → main.py handles it",
        "tg_flow_trigger": "**Trigger Check**: Private Chat / Mentioned / Keywords / Context / Group Whitelist",
        "tg_flow_branch_a": "**Branch A: QA Hit**",
        "tg_flow_branch_a_1": "- Parse qa.txt for fixed answer",
        "tg_flow_branch_a_2": "- Reply directly to Telegram",
        "tg_flow_branch_a_3": "- Write logs and update stats",
        "tg_flow_branch_b": "**Branch B: QA Miss**",
        "tg_flow_branch_b_1": "- Retrieve KB Top-2 as context",
        "tg_flow_branch_b_2": "- Call AI to generate draft",
        "tg_flow_branch_b_3": "- Keyword Pre-check: Allow-list priority; Block/Sensitive → Fallback",
        "tg_flow_branch_b_4": "- Auditor AI (Double-check): Local/Remote, returns PASS/FAIL & suggestions",
        "tg_flow_branch_b_5": "- FAIL retries up to limit, then fallback; PASS sends AI reply",
        "tg_flow_branch_b_6": "- Write audit & system logs, update stats",
        "tg_flow_kw_prio": "**Keyword Priority**",
        "tg_flow_kw_prio_1": "- allow: Direct approval",
        "tg_flow_kw_prio_2": "- block: Direct rejection, triggers fallback",
        "tg_flow_kw_prio_3": "- sensitive: Log & reject (configurable as warning)",
        "tg_flow_fallback": "**Fallback Response**",
        "tg_flow_fallback_1": "- Source: platforms/telegram/audit_fallback.txt",
        "tg_flow_fallback_2": "- Editable in Config page",
        "tg_flow_files": "**Files & Modules**",
        "tg_flow_files_1": "- Main Flow: [main.py](file:///d:/AI%20Talk/main.py)",
        "tg_flow_files_2": "- Audit & Fallback: [audit_manager.py](file:///d:/AI%20Talk/audit_manager.py)",
        "tg_flow_files_3": "- Keywords: [keyword_manager.py](file:///d:/AI%20Talk/keyword_manager.py)",
        "tg_flow_files_4": "- Admin Panel: [admin_multi.py](file:///d:/AI%20Talk/admin_multi.py)",
        "tg_bc_no_cache": "No group cache found. Run bot first.",
        "tg_bc_err_no_group": "Please select at least one group.",
        "tg_bc_err_no_content": "Please enter message content.",
        "tg_bc_fail_prefix": "❌ Broadcast Failed: {}",
        "tg_bc_success_fmt": "✅ Broadcast Done! Success: {}, Failed: {}",
        "tg_bc_no_records": "No broadcast records.",
        "tg_log_cleared": "Cleared",
        "tg_log_clear_fail": "Clear failed: {}",
        "tg_log_tip_load": "Click 'Load Log' to view content.",
        "wa_header": "WhatsApp Auto-reply Bot",
        "wa_qr_title": "WhatsApp Login QR",
        "wa_qr_scan_hint": "Please scan the QR code below with WhatsApp mobile app",
        "wa_qr_caption": "Scan to Login",
        "wa_qr_step1": "Tip: Open WhatsApp > Settings > Linked Devices > Link a Device",
        "wa_qr_step2": "⏳ QR expires in ~20s. Restart bot if expired.",
        "wa_qr_refresh": "🔄 Refresh Status",
        "wa_status_read_err": "Failed to read login status: {}",
        "wa_btn_start": "🚀 Start Bot",
        "wa_btn_stop": "⛔ Stop Bot",
        "wa_btn_restart": "🔄 Restart Bot",
        "wa_restart_success": "Bot Restarted",
        "wa_log_header": "📜 Runtime Logs",
        "wa_log_refresh": "🔄 Refresh Logs",
        "wa_log_empty": "📝 Log is empty, waiting for bot output...",
        "wa_log_missing": "⚠️ Log file not found. Please start the bot first.",
        "wa_log_clear": "🗑️ Clear Logs",
        "wa_log_cleared": "✅ Logs cleared",
        "wa_stats_header": "📊 Statistics",
        "wa_stats_reset": "🗑️ Reset Stats",
        "wa_stats_reset_success": "✅ Stats reset",
        "wa_cfg_header": "⚙️ Configuration",
        "wa_cfg_persona": "AI Persona",
        "wa_cfg_prompt_label": "Edit Prompt",
        "wa_cfg_save_prompt": "💾 Save Persona",
        "wa_cfg_keywords": "Trigger Keywords",
        "wa_cfg_keywords_label": "Group Keywords (One per line)",
        "wa_cfg_save_keywords": "💾 Save Keywords",
        "wa_cfg_switches": "Feature Switches",
        "wa_cfg_private_reply": "Private Reply",
        "wa_cfg_group_reply": "Group Reply",
        "wa_cfg_save_config": "💾 Save Switches",
        "wa_cfg_tip_restart": "💡 Changes take effect immediately, no restart needed",
        "wa_log_file_size": "📁 File size: {} bytes",
        "wa_log_last_updated": "📅 Last updated: {}",
        "wa_log_read_err": "❌ Failed to read log: {}",
        "wa_log_clear_fail": "❌ Clear failed",
        "wa_stats_total_msgs": "Total Messages",
        "wa_stats_total_replies": "Total Replies",
        "wa_stats_success_rate": "Success Rate",
        "wa_stats_failures": "Failures",
        "wa_stats_private": "Private Msgs",
        "wa_stats_group": "Group Msgs",
        "wa_stats_runtime": "⏱️ Uptime: {d}d {h}h {m}m",
        "wa_stats_last_active": "Last Active: {}",
        "wa_stats_read_err": "Failed to read stats: {}",
        "wa_stats_wait": "💡 Stats will be generated after bot runs",
        "orch_header": "Orchestrator",
        "orch_tab_stage": "Stage",
        "orch_tab_persona": "Persona",
        "orch_tab_binding": "Binding",
        "orch_stage_name": "Stage Name",
        "orch_stage_version": "Version",
        "orch_stage_content": "Content (JSON)",
        "orch_btn_save_stage": "Save Stage",
        "orch_persona_name": "Persona Name",
        "orch_persona_version": "Version",
        "orch_persona_content": "Content (JSON)",
        "orch_btn_save_persona": "Save Persona",
        "orch_binding_content": "Stage×Persona→AgentProfile (JSON)",
        "orch_btn_save_binding": "Save Binding",
        "orch_save_success": "✅ Saved",
        "sup_header": "Supervisor Monitor",
        "sup_list_title": "Active Sessions",
        "sup_select_user": "Select Session",
        "sup_force_stage": "Force Stage",
        "sup_force_persona": "Force Persona",
        "sup_handoff": "Human Handoff",
        "sup_btn_apply": "Apply",
        "sup_apply_success": "✅ Applied",
        "sup_route_title": "Recent Routing Decisions",
        "sup_route_col_user": "User",
        "sup_route_col_platform": "Platform",
        "sup_route_col_time": "Time",
        "sup_route_col_decision": "Decision",
        "audit_db_err": "Failed to load logs from DB: {}",
        "audit_save_err": "Error saving config: {}",
        "wa_start_success": "✅ WhatsApp bot started (PID: {})",
        "wa_start_fail": "❌ Start failed: {}",
        "wa_err_no_node": "❌ Node.js not detected. Please install first.",
        "wa_err_missing_deps": "❌ Dependencies missing. Run install.bat/sh first.",
        "wa_stop_success": "✅ WhatsApp bot stopped",
        "wa_stop_not_running": "⚠️ Bot is not running",
        "wa_stop_fail": "❌ Stop failed: {}",

        "acc_save_success": "✅ Account saved",
        "acc_list_title": "Account List",
        "ai_subtitle": "Visual config for AI providers, models & A/B testing",
        "ai_provider": "Provider",
        "ai_base_url": "Base URL",
        "ai_model": "Model Version",
        "ai_weight": "A/B Weight",
        "ai_api_key": "API Key (Masked)",
        "ai_timeout": "Timeout (s)",
        "tg_bc_logs_label": "Logs",
        "tg_bc_exec_err": "Execution error: {}",
        "common_coming_soon": "{} - Coming Soon",
        "common_in_dev": "### 🚧 Under Development",
        "common_planned_features": "**Planned Features:**",
        "common_contact_dev": "💡 Contact developer if you need this platform urgently.",
        "common_dev_progress": "### 📈 Development Progress",
        "common_progress_fmt": "Progress: {}%",
        
        "audit_header": "🛡️ Auditor Config Center",
        "audit_role_warn": "Access restricted to Auditors. Please switch role to Auditor in sidebar.",
        "audit_tab_keywords": "Keyword Management",
        "audit_tab_logs": "Audit Logs",
        "audit_tab_config": "Settings",
        "audit_cfg_enable": "Enable Audit System",
        "audit_cfg_remote": "Use Remote Audit Service",
        "audit_cfg_url": "Remote Server URLs",
        "audit_cfg_remote_help": "Comma separated URLs, first one prioritized",
        "audit_cfg_save": "Save Config",
        "audit_log_col_time": "Time",
        "audit_log_col_role": "Role",
        "audit_log_col_action": "Action",
        "audit_log_col_details": "Details",
        "audit_log_no_data": "No logs found",
        "audit_kw_info": "Keywords configured here take effect immediately for blocking/flagging.",
        "audit_block_header": "#### 🚫 Blocked Keywords",
        "audit_block_caption": "Triggering these will block reply immediately",
        "audit_block_count": "Total {} blocked keywords",
        "audit_block_add": "Add Blocked Keyword",
        "audit_block_add_btn": "Add",
        "audit_block_del_sel": "Select to delete",
        "audit_block_del_btn": "Delete Selected",
        "audit_block_rename_sel": "Select to rename",
        "audit_block_rename_new": "New Name",
        "audit_block_rename_btn": "Rename",
        "audit_sens_header": "#### ⚠️ Sensitive Keywords",
        "audit_sens_caption": "Triggering these will log and reject (or warn)",
        "audit_sens_count": "Total {} sensitive keywords",
        "audit_sens_add": "Add Sensitive Keyword",
        "audit_sens_del_sel": "Select to delete",
        "audit_sens_rename_sel": "Select to rename",
        "audit_allow_header": "#### ✅ Allowed Keywords (Whitelist)",
        "audit_allow_count": "Total {} allowed keywords",
        "audit_allow_add": "Add Allowed Keyword",
        "audit_allow_del_sel": "Select to delete",
        "audit_allow_rename_sel": "Select to rename",
        "audit_log_recent": "Recent Audit Logs",
        "audit_log_refresh": "Refresh Logs",
        
        "api_header": "API Gateway Management",
        "api_route_path": "Route Path /audit /reply",
        "api_route_method": "Method",
        "api_route_auth": "Auth",
        "api_route_rate": "Rate Limit req/min",
        "api_btn_add": "Add/Update Route",
        "api_save_success": "✅ Route Saved",
        "api_list_header": "Route List",

        "sys_header": "System Configuration Automation",
        "sys_env_header": "Environment Config (.env)",
        "sys_status": "Status",
        "sys_status_gen": "Generated",
        "sys_status_not_gen": "Not Generated",
        "sys_file_path": "File: {}",
        "sys_btn_gen_env": "Generate/Update .env",
        "sys_success_env": "✅ .env Generated/Updated",
        "sys_session_header": "Session File Generation",
        "sys_btn_init_session": "Silent Init Session Files",
        "sys_success_session": "✅ Session Files Initialized",
        "sys_secret_header": "Secrets Encryption & View",
        "sys_secret_caption": "Masked by default; 2FA required to view.",
        "sys_btn_gen_code": "Generate 2FA Code",
        "sys_code_info": "Generated. Enter code to view.",
        "sys_input_code": "Enter 2FA Code",
        "sys_btn_view": "View Plaintext",
        "sys_success_view": "✅ Verified (Session Valid)",
        "sys_err_code": "Invalid Code",

        "acc_header": "Account Management",
        "acc_tenant": "Current Tenant: {}",
        "acc_subtitle": "Centralized account entry, grouping, and tagging",
        "acc_col_platform": "Platform",
        "acc_col_username": "Username/ID",
        "acc_col_group": "Group",
        "acc_col_tags": "Tags (comma separated)",
        "acc_col_refresh": "Refresh Interval (min)",
        "acc_btn_add": "Add/Update Account",
        
        "cs_title": "🚧 Platform Under Development",
        "cs_desc": "**{}** is under development, stay tuned!",
        "cs_plan_title": "**Planned Features:**",
        "cs_plan_1": "✅ Auto Reply",
        "cs_plan_2": "✅ Context Memory",
        "cs_plan_3": "✅ Broadcast",
        "cs_plan_4": "✅ Web Management",
        "cs_plan_5": "✅ Stats & Reports",
        "cs_eta": "**ETA:** TBD",
        "cs_contact": "💡 Contact developer if you need this urgently.",
        "cs_progress_title": "### 📈 Progress",
        "cs_progress_caption": "Completion: {}%",

        "wa_status_running": "🟢 Running",
        "wa_status_stopped": "🔴 Stopped",
    }
}
def tr(key):
    lang = st.session_state.get("lang", "zh")
    return I18N.get(lang, I18N["zh"]).get(key, key)

def _render_scope_hint(scope_text: str):
    if scope_text:
        st.markdown(f"**生效范围：{scope_text}**")

def format_time(dt_obj, tz_name=None):
    """格式化时间显示，支持多时区"""
    if not dt_obj:
        return "-"
    if not tz_name:
        tz_name = st.session_state.get("timezone", "Asia/Shanghai")
    
    if isinstance(dt_obj, str):
        try:
            dt_obj = datetime.fromisoformat(dt_obj)
        except:
            return dt_obj
            
    try:
        if dt_obj.tzinfo is None:
            # 假设存储的时间是 UTC 或本地无时区时间，先作为 UTC 处理
            # 如果是本地时间且无时区，pytz.utc.localize 可能会有偏差，但在本项目中
            # 大部分时间是 isoformat (可能含时区也可能不含)
            # 简单起见，统一视为 UTC
            dt_obj = pytz.utc.localize(dt_obj)
        
        target_tz = pytz.timezone(tz_name)
        dt_local = dt_obj.astimezone(target_tz)
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt_obj)

# 平台配置
PLATFORMS = {
    'ai_learning': {
        'name': 'AI学习中心',
        'icon': '🧪',
        'color': '#7c3aed',
        'status': 'available',
        'description': '对话数据清洗与可学习集管理',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'skills': {
        'name': '技能中心',
        'icon': '🧩',
        'color': '#2563eb',
        'status': 'available',
        'description': '技能配置与绑定业务线',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'knowledge': {
        'name': '📚',
        'icon': '📚',
        'color': '#8b5cf6',
        'status': 'available',
        'description': '知识库配置与检索',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'audit': {
        'name': '🛡️',
        'icon': '🛡️',
        'color': '#FF5733',
        'status': 'available',
        'description': '关键词与日志管理',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'business': {
        'name': '商业化运营',
        'icon': '📊',
        'color': '#F59E0B',
        'status': 'available',
        'description': '订阅/计费/数据看板',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'telegram': {
        'name': 'Telegram',
        'icon': '📱',
        'color': '#0088cc',
        'status': 'available',  # available, unavailable, coming_soon
        'description': '全功能支持 - 私聊/群聊/频道',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'whatsapp': {
        'name': 'WhatsApp',
        'icon': '💬',
        'color': '#25D366',
        'status': 'available',
        'description': '✅ 可用 - 私聊/群聊自动回复',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'accounts': {
        'name': '账号管理',
        'icon': '👥',
        'color': '#4b5563',
        'status': 'available',
        'description': '集中录入与分组/标签管理',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'ai_config': {
        'name': 'AGNT AI配置中心',
        'icon': '🧠',
        'color': '#0ea5e9',
        'status': 'available',
        'description': 'AI服务商接入与A/B测试',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'api_gateway': {
        'name': 'API接口管理中心',
        'icon': '🛣️',
        'color': '#16a34a',
        'status': 'available',
        'description': '统一网关/权限/流控/日志',
        'roles': ['SuperAdmin']
    },
    'sys_config': {
        'name': '系统配置自动化',
        'icon': '🧩',
        'color': '#0f766e',
        'status': 'available',
        'description': '环境/会话/密钥自动化',
        'roles': ['SuperAdmin']
    },
    'system_admin': {
        'name': '系统管理',
        'icon': '🛠️',
        'color': '#111827',
        'status': 'available',
        'description': '系统账号/IP白名单/登录日志/升级',
        'roles': ['SuperAdmin']
    },

    'twitter': {
        'name': 'Twitter/X',
        'icon': '🐦',
        'color': '#1DA1F2',
        'status': 'coming_soon',
        'description': '规划中 - DM + 提及回复',
        'roles': ['SuperAdmin']
    },
    'facebook': {
        'name': 'Facebook',
        'icon': '📘',
        'color': '#1877F2',
        'status': 'coming_soon',
        'description': '规划中 - Page/Group',
        'roles': ['SuperAdmin']
    },
    'messenger': {
        'name': 'Messenger',
        'icon': '💬',
        'color': '#00B2FF',
        'status': 'coming_soon',
        'description': '规划中 - Auto Reply',
        'roles': ['SuperAdmin']
    },
    'wechat': {
        'name': 'WeChat',
        'icon': '🟢',
        'color': '#07C160',
        'status': 'coming_soon',
        'description': '规划中 - 公众号/企业微信',
        'roles': ['SuperAdmin']
    },
    'instagram': {
        'name': 'Instagram',
        'icon': '📸',
        'color': '#E1306C',
        'status': 'coming_soon',
        'description': '规划中 - DM',
        'roles': ['SuperAdmin']
    },
    'discord': {
        'name': 'Discord',
        'icon': '💜',
        'color': '#5865F2',
        'status': 'coming_soon',
        'description': '规划中 - 服务器 Bot'
    },
    'orchestrator': {
        'name': 'AI剧本配置',
        'icon': '🎼',
        'color': '#3b82f6',
        'status': 'available',
        'description': '流程/人设/绑定与评估',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'supervisor': {
        'name': '主管决策',
        'icon': '👀',
        'color': '#22c55e',
        'status': 'available',
        'description': '会话与决策记录',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'help_center': {
        'name': '帮助中心',
        'icon': '🆘',
        'color': '#ef4444',
        'status': 'available',
        'description': '文档与使用指南',
        'roles': ['SuperAdmin', 'BusinessAdmin']
    },
    'system_status': {
        'name': '系统状态',
        'icon': '📈',
        'color': '#10b981',
        'status': 'available',
        'description': '系统运行健康度看板',
        'roles': ['SuperAdmin']
    },
    'test_cases': {
        'name': '测试用例集',
        'icon': '🧪',
        'color': '#f97316',
        'status': 'available',
        'description': '回归测试用例与一键执行',
        'roles': ['SuperAdmin']
    }
}

@st.cache_data(ttl=2)
def _load_raw_trace_data(path):
    path = str(path)
    if not os.path.exists(path):
        return []
    items = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    items.append(obj)
                except:
                    continue
    except:
        return []
    return items

def _read_trace_jsonl(path, window_minutes=5):
    try:
        items = _load_raw_trace_data(path)
        if not items:
            return []
            
        now = datetime.now()
        cutoff = now.timestamp() - window_minutes * 60
        
        result = []
        for obj in items:
            ts = obj.get("timestamp")
            if ts:
                try:
                    tdt = datetime.fromisoformat(ts.replace("Z",""))
                    if tdt.timestamp() >= cutoff:
                        result.append(obj)
                except:
                    result.append(obj) # Keep if no valid time (safe fallback)
            else:
                result.append(obj)
        return result
    except:
        return []

def _p95(values):
    if not values:
        return 0.0
    vals = sorted(values)
    idx = int(0.95 * (len(vals)-1))
    return float(vals[idx])

def _status_by_threshold(error_rate, p95_latency_ms):
    if error_rate is None:
        return "Gray"
    # 优先判断错误率
    if error_rate >= 0.05:
        return "Red"
    if error_rate >= 0.01:
        return "Yellow"
    # 其次判断延迟
    if p95_latency_ms >= 3000:
        return "Yellow"
    return "Green"

def _node_color(status):
    return {"Green":"#34d399","Yellow":"#facc15","Red":"#ef4444","Gray":"#9ca3af"}.get(status, "#9ca3af")

def render_system_status_panel():
    st.header("🧭 系统状态")
    _render_scope_hint("当前租户全平台生效（只读看板）")
    tenant_id = st.session_state.get("tenant","default")
    window = st.selectbox("时间窗口", ["5min","15min","1h"], index=0)
    win_map = {"5min":5, "15min":15, "1h":60}
    window_minutes = win_map.get(window, 5)
    refresh_ms = st.number_input("自动刷新间隔(ms)", value=10000, step=1000)
    if st.button("手动刷新"):
        try:
            st.rerun()
        except Exception:
            pass
    trace_path = os.path.join(BASE_DIR, "platforms", "telegram", "logs", "trace.jsonl")
    logs = _read_trace_jsonl(str(trace_path), window_minutes)
    by_tid = {}
    for e in logs:
        tid = e.get("trace_id")
        if not tid:
            continue
        by_tid.setdefault(tid, []).append(e)
    for tid in by_tid:
        by_tid[tid].sort(key=lambda x: x.get("timestamp",""))
    nodes = [
        ("消息入口","MSG_RECEIVED"),
        ("加载会话状态","STATE_LOADED"),
        ("主管决策","SUPERVISOR_DECIDED"),
        ("知识库检索","KB_RETRIEVED"),
        ("生成回复","STAGE_AGENT_GENERATED"),
        ("风格守卫","STYLE_GUARD"),
        ("审核/关键词","AUDIT_RESULT"),
        ("发送回复","REPLY_SENT"),
        ("更新会话状态","STATE_UPDATED"),
    ]
    seq = [n[1] for n in nodes]
    node_metrics = {}
    step_latency = {ev: [] for _, ev in nodes}
    total_turns = len(by_tid)
    for tid, events in by_tid.items():
        # Build event type set with synonyms
        types = [e.get("event_type") for e in events]
        type_set = set(types)
        # Normalize Style Guard synonyms
        if "STYLE_GUARD_APPLIED" in type_set or "STYLE_GUARD" in type_set:
            type_set.add("STYLE_GUARD")
        # Normalize Audit presence
        if {"AUDIT_PRIMARY","AUDIT_SECONDARY","FINAL_ACTION"} & type_set:
            type_set.add("AUDIT_RESULT")
        
        # Determine branch: 
        # 1. QA Branch: QA_HIT exists
        # 2. AI Branch: AI pipeline events exist (STAGE_AGENT_GENERATED etc.)
        qa_branch = "QA_HIT" in type_set
        ai_branch = bool({"STAGE_AGENT_GENERATED","STYLE_GUARD","AUDIT_RESULT"} & type_set)
        
        errs = [e for e in events if e.get("event_type") in ["ERROR","ORCHESTRATION_ERROR"]]
        for name, ev in nodes:
            # Node expectation rules
            expected = True
            if ev in ("KB_RETRIEVED","STAGE_AGENT_GENERATED","STYLE_GUARD","AUDIT_RESULT"):
                # These are AI-specific, skip if it's a QA branch (unless mixed, but usually exclusive)
                expected = ai_branch and not qa_branch
            
            # Special case: Reply Send is expected in both branches
            if ev == "REPLY_SENT":
                expected = True

            ok = ev in type_set
            node_metrics.setdefault(ev, {"total":0,"fail":0})
            
            # Count only traces where node is expected
            if expected:
                node_metrics[ev]["total"] += 1
                # Failure: errors, or expected-but-missing
                if errs or not ok:
                    node_metrics[ev]["fail"] += 1
        idx_map = {e.get("event_type"): i for i, e in enumerate(events)}
        for i, ev in enumerate(seq):
            if ev in idx_map:
                cur_idx = idx_map[ev]
                if i+1 < len(seq):
                    nxt = seq[i+1]
                    if nxt in idx_map:
                        t1 = events[cur_idx].get("timestamp")
                        t2 = events[idx_map[nxt]].get("timestamp")
                        try:
                            dt1 = datetime.fromisoformat(t1.replace("Z",""))
                            dt2 = datetime.fromisoformat(t2.replace("Z",""))
                            dms = (dt2 - dt1).total_seconds() * 1000.0
                            if dms >= 0:
                                step_latency[ev].append(dms)
                        except:
                            pass
    per_node = []
    for name, ev in nodes:
        m = node_metrics.get(ev, {"total":0,"fail":0})
        total = max(1, m["total"])
        fail_rate = m["fail"]/total
        p95 = _p95(step_latency.get(ev, []))
        status = _status_by_threshold(fail_rate, p95)
        per_node.append({"node":name,"event":ev,"status":status,"success_rate":round(1.0-fail_rate,4),"err_count":m["fail"],"p95_latency":int(p95)})
    overall = "Healthy"
    if any(x["status"]=="Red" for x in per_node):
        overall = "Outage"
    elif any(x["status"]=="Yellow" for x in per_node):
        overall = "Degraded"
    msg_in = sum(1 for e in logs if e.get("event_type")=="MSG_RECEIVED")
    minutes = max(1, window_minutes)
    throughput = int(msg_in/minutes)
    lat_list = []
    for tid, events in by_tid.items():
        idx = {e.get("event_type"): i for i,e in enumerate(events)}
        if "MSG_RECEIVED" in idx and "REPLY_SENT" in idx:
            t1 = events[idx["MSG_RECEIVED"]].get("timestamp")
            t2 = events[idx["REPLY_SENT"]].get("timestamp")
            try:
                dt1 = datetime.fromisoformat(t1.replace("Z",""))
                dt2 = datetime.fromisoformat(t2.replace("Z",""))
                lat_list.append((dt2-dt1).total_seconds()*1000.0)
            except:
                pass
    avg_latency = int(sum(lat_list)/max(1,len(lat_list))) if lat_list else 0
    fail_sorted = sorted(per_node, key=lambda x: x["err_count"], reverse=True)
    top3 = [x["node"] for x in fail_sorted[:3]]
    cols = st.columns(4)
    cols[0].metric("Overall Status", overall)
    cols[1].metric("消息吞吐(msg/min)", throughput)
    cols[2].metric("平均延迟(ms)", avg_latency)
    cols[3].metric("失败 Top3 节点", ", ".join(top3) if top3 else "-")
    st.divider()
    grid_cols = st.columns(3)
    for i, nd in enumerate(per_node):
        c = grid_cols[i%3]
        with c:
            st.markdown(f"**{nd['node']}**")
            color = _node_color(nd["status"])
            st.markdown(f"<div style='display:inline-block;width:12px;height:12px;border-radius:999px;background:{color};margin-right:6px;'></div><span>{nd['status']}</span>", unsafe_allow_html=True)
            st.caption(f"成功率: {int(nd['success_rate']*100)}%")
            st.caption(f"错误数: {nd['err_count']}")
            st.caption(f"p95延迟: {nd['p95_latency']}ms")
            if st.button("详情", key=f"detail_{nd['event']}"):
                fails = []
                for tid, events in by_tid.items():
                    types = [e.get("event_type") for e in events]
                    if nd["event"] not in types:
                        fails.append({"trace_id":tid,"reason":"missing_event"})
                    if any(e.get("event_type") in ["ERROR","ORCHESTRATION_ERROR"] for e in events):
                        fails.append({"trace_id":tid,"reason":"error"})
                st.write("最近失败记录")
                for item in fails[:20]:
                    st.write(item)
    st.divider()
    db_health = "Green"
    try:
        _ = db.get_dashboard_metrics(tenant_id, days=1)
    except:
        db_health = "Red"
    ai_health = "Green"
    try:
        base = os.getenv("AI_BASE_URL") or ""
        if base:
            import httpx
            _v = (os.getenv("HTTPX_VERIFY_SSL") or "").strip().lower()
            _verify = False if _v in ("0","false","no") else True
            with httpx.Client(verify=_verify, timeout=5) as hc:
                r = hc.get(base)
                if r.status_code >= 500:
                    ai_health = "Red"
        else:
            ai_health = "Yellow"
    except:
        ai_health = "Red"
    infra_cols = st.columns(2)
    with infra_cols[0]:
        st.markdown("**Persistence/DB**")
        st.markdown(f"<div style='display:inline-block;width:12px;height:12px;border-radius:999px;background:{_node_color(db_health)};margin-right:6px;'></div><span>{db_health}</span>", unsafe_allow_html=True)
    with infra_cols[1]:
        st.markdown("**AI Provider**")
        st.markdown(f"<div style='display:inline-block;width:12px;height:12px;border-radius:999px;background:{_node_color(ai_health)};margin-right:6px;'></div><span>{ai_health}</span>", unsafe_allow_html=True)

TG_GROUP_CACHE_FILE = os.path.join(BASE_DIR, "platforms", "telegram", "group_cache.json")
TG_SELECTED_GROUPS_FILE = os.path.join(BASE_DIR, "platforms", "telegram", "selected_groups.json")
TG_LOG_DIR = os.path.join(BASE_DIR, "platforms", "telegram", "logs")
TG_SYSTEM_LOG_FILE = os.path.join(TG_LOG_DIR, "system.log")
TG_PRIVATE_LOG_FILE = os.path.join(TG_LOG_DIR, "private.log")
TG_GROUP_LOG_FILE = os.path.join(TG_LOG_DIR, "group.log")

def load_tg_group_cache():
    try:
        with open(TG_GROUP_CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    groups = []
    for chat_id, info in data.items():
        try:
            cid = int(chat_id)
        except Exception:
            continue
        title = ""
        last_seen = ""
        if isinstance(info, dict):
            title = info.get("title") or info.get("name") or ""
            last_seen = info.get("last_seen") or ""
        groups.append({"id": cid, "title": title, "last_seen": last_seen})
    groups.sort(key=lambda item: (item["title"] or "", item["id"]))
    return groups

def load_tg_selected_group_ids():
    try:
        with open(TG_SELECTED_GROUPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ids = data.get("selected_ids", [])
        return {int(x) for x in ids}
    except Exception:
        return set()

def save_tg_selected_group_ids(selected_ids):
    os.makedirs(os.path.dirname(TG_SELECTED_GROUPS_FILE), exist_ok=True)
    with open(TG_SELECTED_GROUPS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"selected_ids": list(selected_ids)}, f, ensure_ascii=False, indent=2)
    try:
        log_admin_op("tg_whitelist_write", {"count": len(selected_ids)})
    except Exception:
        pass

def format_group_label(group_info):
    title = group_info.get("title") or "未命名群组"
    return f"{title} ({group_info.get('id')})"

def read_log_file(file_path, max_lines=200):
    try:
        if not os.path.exists(file_path):
            return "暂无日志文件"
        if os.path.getsize(file_path) == 0:
            return "日志文件为空"
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        if not lines:
            return "日志文件为空"
        return "".join(lines[-max_lines:])
    except Exception as exc:
        return f"读取日志失败: {exc}"

def _ensure_admin_session():
    admin_session = "admin_session"
    if not os.path.exists(f"{admin_session}.session") and os.path.exists("userbot_session.session"):
        try:
            shutil.copy("userbot_session.session", f"{admin_session}.session")
        except Exception:
            pass
    return admin_session

async def send_broadcast_ids_with_interval(chat_ids, message, interval_seconds, group_map=None, progress_callback=None):
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError, PeerFloodError

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    if not all([api_id, api_hash]):
        return [], 0, 0, "Missing TELEGRAM_API_ID/TELEGRAM_API_HASH in .env"

    session_name = _ensure_admin_session()
    client = TelegramClient(session_name, int(api_id), api_hash)
    try:
        await asyncio.wait_for(client.connect(), timeout=10)
        if not await client.is_user_authorized():
            await client.disconnect()
            return [], 0, 0, "未登录 Telegram，请先完成登录"
    except Exception as exc:
        return [], 0, 0, f"连接 Telegram 失败: {exc}"

    records = []
    success = 0
    failed = 0
    total = len(chat_ids)

    for idx, chat_id in enumerate(chat_ids, 1):
        name = None
        if group_map:
            name = group_map.get(chat_id)
        label = name or str(chat_id)
        if progress_callback:
            progress_callback(idx, total, label)
        try:
            entity = await client.get_entity(chat_id)
            await client.send_message(entity, message)
            records.append({"group": label, "id": chat_id, "status": "success", "error": ""})
            success += 1
        except FloodWaitError as e:
            wait_time = getattr(e, "seconds", 0)
            records.append({"group": label, "id": chat_id, "status": "failed", "error": f"限流等待 {wait_time}s"})
            failed += 1
            await asyncio.sleep(wait_time)
        except PeerFloodError:
            records.append({"group": label, "id": chat_id, "status": "failed", "error": "触发 PeerFlood，已中止"})
            failed += 1
            break
        except Exception as exc:
            err_text = str(exc)
            if "database is locked" in err_text:
                records.append({"group": label, "id": chat_id, "status": "failed", "error": "数据库被锁定，请先停止机器人"})
                failed += 1
                break
            records.append({"group": label, "id": chat_id, "status": "failed", "error": err_text})
            failed += 1
        if idx < total and interval_seconds > 0:
            await asyncio.sleep(interval_seconds)

    await client.disconnect()
    return records, success, failed, None

def load_platform_config(platform):
    """加载平台配置（支持租户隔离）"""
    tenant_id = st.session_state.get('tenant', 'default')
    
    # 优先加载租户专属配置
    tenant_config_file = f"data/tenants/{tenant_id}/platforms/{platform}/config.json"
    if os.path.exists(tenant_config_file):
        try:
            with open(tenant_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
            
    # 如果租户配置不存在，回退到全局默认配置（可选，或直接返回空）
    # 策略：对于新租户，返回空配置，确保是“全新、空配置”的状态
    # global_config_file = f"platforms/{platform}/config.json"
    # if os.path.exists(global_config_file):
    #     try:
    #         with open(global_config_file, 'r', encoding='utf-8') as f:
    #             return json.load(f)
    #     except:
    #         pass
            
    return {}

def save_platform_config(platform, config):
    """保存平台配置（支持租户隔离）"""
    tenant_id = st.session_state.get('tenant', 'default')
    
    # 保存到租户专属目录
    config_file = f"data/tenants/{tenant_id}/platforms/{platform}/config.json"
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    try:
        log_admin_op("platform_config_save", {"platform": platform, "tenant": tenant_id})
    except Exception:
        pass

def render_platform_selector():
    st.sidebar.markdown(f"### 🌐 {tr('nav_platform')}")
    selected_platform = st.session_state.get('selected_platform', 'telegram')
    current_role = st.session_state.get('user_role', 'SuperAdmin')
    groups = [
        ("🤖 AI 配置中心", ["ai_config", "orchestrator", "supervisor", "skills", "ai_learning"]),
        ("📱 平台配置", ["telegram", "whatsapp", "facebook", "messenger", "wechat", "instagram", "twitter", "discord"]),
        ("💼 业务管理", ["business", "accounts"]),
        ("📚 数据管理", ["knowledge", "audit"]),
        ("🛠️ 系统管理", ["system_admin", "sys_config", "api_gateway", "system_status", "test_cases"]),
        ("🆘 文档与帮助", ["help_center"])
    ]
    for g_title, g_items in groups:
        visible_items = []
        for platform_id in g_items:
            info = PLATFORMS.get(platform_id)
            if not info:
                continue
            roles = info.get("roles")
            if roles and current_role not in roles:
                continue
            visible_items.append(platform_id)
        if not visible_items:
            continue
        with st.sidebar.expander(g_title, expanded=selected_platform in g_items):
            for platform_id in visible_items:
                if platform_id not in PLATFORMS:
                    continue
                info = PLATFORMS[platform_id]
                roles = info.get('roles')
                if roles and current_role not in roles:
                    continue
                icon = info.get('icon', '')
                tr_name = tr(f"plat_{platform_id}")
                if tr_name == f"plat_{platform_id}":
                    tr_name = info['name']
                status = info.get('status')
                dot = "🟢" if status == "available" else ("🟡" if status == "coming_soon" else "🔴")
                label = f"{icon} {tr_name} {dot}"
                is_selected = (selected_platform == platform_id)
                if st.button(
                    label,
                    key=f"select_{platform_id}",
                    disabled=(status != 'available'),
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.selected_platform = platform_id
                    st.rerun()
            # 在“文档与帮助”子菜单中插入“文档与目录”选项，位置在全局“系统信息”之前
            if g_title.startswith("🆘 文档与帮助") and selected_platform == "help_center":
                docs_root = os.path.join(BASE_DIR, "docs", "help_center", "v1.0")
                lang = st.session_state.get("lang", "zh")
                lang_dir = "zh_CN" if lang == "zh" else "en_US"
                if not os.path.exists(os.path.join(docs_root, lang_dir)):
                    lang_dir = "zh_CN"
                current_dir = os.path.join(docs_root, lang_dir)
                if os.path.exists(current_dir):
                    files = [f for f in os.listdir(current_dir) if f.endswith(".md")]
                    files.sort()
                    st.markdown("#### 📚 文档与目录")
                    st.radio("选择文档", files, format_func=lambda x: x.replace(".md", "").title(), key="doc_selector")
    return selected_platform

KB_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
KB_FILES_DIR = os.path.join(KB_DIR, "files")
KB_DB_FILE = os.path.join(KB_DIR, "db.json")

def ensure_kb_dirs():
    os.makedirs(KB_FILES_DIR, exist_ok=True)
    if not os.path.exists(KB_DB_FILE):
        with open(KB_DB_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": []}, f, ensure_ascii=False, indent=2)

def load_kb_db():
    ensure_kb_dirs()
    try:
        with open(KB_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            return data
    except Exception:
        pass
    return {"items": []}

def save_kb_db(db):
    ensure_kb_dirs()
    with open(KB_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def _read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="gbk") as f:
                return f.read()
        except Exception:
            return ""
    except Exception:
        return ""

def extract_content_from_upload(upload, filename):
    name_lower = (filename or "").lower()
    content = ""
    parse_note = ""
    if name_lower.endswith((".txt", ".md")):
        try:
            content = upload.getvalue().decode("utf-8", errors="ignore")
        except Exception:
            content = upload.getvalue().decode("latin-1", errors="ignore")
    elif name_lower.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(upload)
            pages = []
            for i in range(len(reader.pages)):
                text = reader.pages[i].extract_text()
                if text:
                    pages.append(f"# PDF Page {i+1}\n{text}")
            content = "\n\n".join(pages).strip()
            parse_note = "parsed:pdf"
        except Exception as e:
            parse_note = f"unparsed:pdf:{e}"
            content = ""
    elif name_lower.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(upload)
            content = "\n".join([p.text for p in doc.paragraphs]).strip()
            parse_note = "parsed:docx"
        except Exception as e:
            parse_note = f"unparsed:docx:{e}"
            content = ""
    elif name_lower.endswith(".xlsx"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(upload, read_only=True, data_only=True)
            texts = []
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    items = [str(cell) for cell in row if cell is not None]
                    if items:
                        texts.append(" | ".join(items))
            content = "\n".join(texts).strip()
            parse_note = "parsed:xlsx"
        except Exception as e:
            parse_note = f"unparsed:xlsx:{e}"
            content = ""
    else:
        try:
            content = upload.getvalue().decode("utf-8", errors="ignore")
        except Exception:
            content = ""
        parse_note = "unknown_format"
    return content, parse_note

def render_kb_panel():
    ensure_kb_dirs()
    st.header(f"📚 {tr('kb_header')}")
    _render_scope_hint("当前租户全平台生效")
    
    tenant_id = st.session_state.get("tenant", "default")
    
    if st.session_state.get("kb_import_success"):
        st.success(st.session_state.get("kb_import_success"))
        del st.session_state["kb_import_success"]
    if st.session_state.get("kb_text_success"):
        st.success(st.session_state.get("kb_text_success"))
        del st.session_state["kb_text_success"]
        
    tabs = st.tabs([tr("kb_tab_manage"), tr("kb_tab_import"), tr("kb_tab_test"), tr("kb_tab_settings")])

    with tabs[0]:
        st.subheader(tr("kb_list_title"))
        # DB Migration: Use SQLite instead of JSON
        items = db.get_kb_items(tenant_id)
        
        if not items:
            st.info(tr("kb_no_items"))
        else:
            cols = st.columns([2, 2, 2, 2, 2])
            cols[0].markdown(f"**{tr('kb_col_title')}**")
            cols[1].markdown(f"**{tr('kb_col_category')}**")
            cols[2].markdown(f"**{tr('kb_col_tags')}**")
            cols[3].markdown(f"**{tr('kb_col_source')}**")
            cols[4].markdown(f"**{tr('kb_col_action')}**")
            
            for idx, it in enumerate(items):
                # SQLite returns row dicts
                t = it.get("title","")
                c = it.get("category","")
                tags_raw = it.get("tags") or ""
                # Tags stored as string in DB for simplicity, or we parse if JSON
                # Assuming simple string or JSON string. If JSON list:
                tags = []
                if isinstance(tags_raw, list):
                    tags = tags_raw
                elif isinstance(tags_raw, str):
                    if tags_raw.startswith("["):
                        try: tags = json.loads(tags_raw)
                        except: tags = [tags_raw]
                    else:
                        tags = [x.strip() for x in tags_raw.split(",") if x.strip()]
                        
                src = it.get("source_file","")
                
                cols = st.columns([2,2,2,2,2])
                cols[0].write(t or "(Unamed)")
                cols[1].write(c or "-")
                cols[2].write(", ".join(tags) if tags else "-")
                src_disp = os.path.basename(src) if src else "-"
                cols[3].write(src_disp)
                with cols[4]:
                    edit_key = f"kb_edit_{it['id']}" # Use ID for uniqueness
                    del_key = f"kb_del_{it['id']}"
                    
                    if st.button(tr("common_edit"), key=edit_key):
                        st.session_state.kb_edit_id = it['id']
                        st.session_state.kb_edit_item = it # Cache item for editing
                        st.rerun()
                        
                    if st.button(tr("common_delete"), key=del_key):
                        db.delete_kb_item(it['id'])
                        log_admin_op("kb_delete", {"id": it.get('id'), "title": it.get('title')})
                        st.success(tr("common_success"))
                        st.rerun()
                        
        st.divider()
        st.subheader(tr("kb_new_item"))
        title = st.text_input(tr("kb_input_title"), key="kb_new_title")
        category = st.text_input(tr("kb_input_cat"), key="kb_new_category")
        tags = st.text_input(tr("kb_input_tags"), key="kb_new_tags")
        content = st.text_area(tr("kb_input_content"), height=180, key="kb_new_content")
        
        if st.button(tr("kb_btn_save"), type="primary", key="kb_save_text"):
            if not title.strip() and not content.strip():
                st.error(tr("kb_err_empty"))
            else:
                new_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                now_iso = datetime.now().isoformat()
                # Tags list to string/json
                tags_list = [t.strip() for t in tags.split(",") if t.strip()]
                tags_str = json.dumps(tags_list, ensure_ascii=False)
                
                item = {
                    "id": new_id,
                    "tenant_id": tenant_id,
                    "title": title.strip(),
                    "category": category.strip(),
                    "tags": tags_str,
                    "content": content.strip(),
                    "source_file": "",
                    "created_at": now_iso,
                    "updated_at": now_iso
                }
                db.add_kb_item(item)
                log_admin_op("kb_add", {"id": new_id, "title": title.strip()})
                st.session_state["kb_text_success"] = f"{tr('common_success')}: {title}"
                st.rerun()

        if "kb_edit_id" in st.session_state and st.session_state.kb_edit_id:
            st.divider()
            st.subheader(tr("kb_edit_title"))
            # Fetch fresh or use cached
            edit_id = st.session_state.kb_edit_id
            # Find item from current list or DB (simplified: use cached if available, else fetch)
            it = st.session_state.get("kb_edit_item", {})
            
            # Helper to safely get value
            def get_val(k, default=""):
                return it.get(k, default)
            
            # Tags handling
            etags_val = get_val("tags", "")
            if isinstance(etags_val, list):
                etags_val = ",".join(etags_val)
            elif isinstance(etags_val, str) and etags_val.startswith("["):
                 try: 
                    l = json.loads(etags_val)
                    etags_val = ",".join(l)
                 except: pass
            
            etitle = st.text_input(tr("kb_input_title"), value=get_val("title"), key="kb_edit_title_in")
            ecategory = st.text_input(tr("kb_input_cat"), value=get_val("category"), key="kb_edit_cat_in")
            etags = st.text_input(tr("kb_input_tags"), value=etags_val, key="kb_edit_tags_in")
            econtent = st.text_area(tr("kb_input_content"), value=get_val("content"), height=180, key="kb_edit_content_in")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button(tr("common_save"), type="primary", key="kb_edit_save"):
                    tags_list = [t.strip() for t in etags.split(",") if t.strip()]
                    tags_str = json.dumps(tags_list, ensure_ascii=False)
                    
                    updates = {
                        "title": etitle.strip(),
                        "category": ecategory.strip(),
                        "tags": tags_str,
                        "content": econtent.strip(),
                        "updated_at": datetime.now().isoformat()
                    }
                    db.update_kb_item(edit_id, updates)
                    log_admin_op("kb_update", {"id": edit_id, "title": etitle.strip()})
                    st.success(tr("common_success"))
                    del st.session_state["kb_edit_id"]
                    del st.session_state["kb_edit_item"]
                    st.rerun()
            with c2:
                if st.button(tr("common_cancel"), key="kb_edit_cancel"):
                    del st.session_state["kb_edit_id"]
                    del st.session_state["kb_edit_item"]
                    st.rerun()

    with tabs[1]:
        st.subheader(tr("kb_import_header"))
        uploaded = st.file_uploader(tr("kb_import_desc"), type=["txt","md","pdf","docx","xlsx"], key="kb_file_uploader")
        if uploaded:
            safe_name = uploaded.name
            ensure_kb_dirs()
            dest_path = os.path.join(KB_FILES_DIR, safe_name)
            with open(dest_path, "wb") as f:
                f.write(uploaded.getvalue())
            content, note = extract_content_from_upload(uploaded, safe_name)
            st.info(f"Parse Note: {note or 'ok'}")
            
            title = st.text_input(tr("kb_input_title"), value=os.path.splitext(safe_name)[0], key="kb_import_title")
            category = st.text_input(tr("kb_input_cat"), key="kb_import_category")
            tags = st.text_input(tr("kb_input_tags"), key="kb_import_tags")
            preview = st.text_area(tr("kb_import_preview"), value=content, height=200, key="kb_import_preview_area")
            
            if st.button(tr("kb_import_save"), type="primary", key="kb_import_save_btn"):
                new_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                now_iso = datetime.now().isoformat()
                tags_list = [t.strip() for t in tags.split(",") if t.strip()]
                tags_str = json.dumps(tags_list, ensure_ascii=False)
                
                item = {
                    "id": new_id,
                    "tenant_id": tenant_id,
                    "title": title.strip(),
                    "category": category.strip(),
                    "tags": tags_str,
                    "content": preview.strip(),
                    "source_file": os.path.relpath(dest_path, BASE_DIR),
                    "created_at": now_iso,
                    "updated_at": now_iso
                }
                db.add_kb_item(item)
                log_admin_op("kb_import", {"id": new_id, "title": title.strip(), "source_file": safe_name})
                st.session_state["kb_import_success"] = f"{tr('common_success')}: {title}"
                st.rerun()

    with tabs[2]:
        st.subheader(tr("kb_test_header"))
        query = st.text_input(tr("kb_test_input"), key="kb_query")
        topn = st.number_input(tr("kb_test_topn"), min_value=1, max_value=10, value=3, step=1, key="kb_topn")
        if st.button(tr("kb_test_btn"), key="kb_search"):
            # Simple in-memory search for now, replacing retrieve_kb_context which used list
            # Ideally move search logic to BusinessCore or Database (if using vector search later)
            # For now, replicate simple keyword/similarity matching using loaded items
            
            items = db.get_kb_items(tenant_id)
            if not items:
                st.warning(tr("kb_no_items"))
            else:
                import time
                t0 = time.time()
                # Basic mock search: keyword match in title/content
                # In real prod, this should use embeddings. 
                # Preserving existing logic if possible, but existing used `main.retrieve_kb_context`.
                # Let's try to reuse `main.retrieve_kb_context` but pass it the dict list
                
                try:
                    from main import retrieve_kb_context
                    ranked = retrieve_kb_context(query, items, topn=int(topn))
                except Exception:
                    ranked = [it for it in items if query.lower() in (it.get('title','') + it.get('content','')).lower()]
                    ranked = ranked[:int(topn)]

                elapsed_ms = (time.time() - t0) * 1000
                st.info(f"Time: {elapsed_ms:.2f} ms, Found: {len(ranked)}")
                for it in ranked:
                    tags_disp = it.get('tags','')
                    if isinstance(tags_disp, str) and tags_disp.startswith("["):
                         try: tags_disp = ", ".join(json.loads(tags_disp))
                         except: pass
                    
                    st.write(f"- **{it.get('title','(Unamed)')}** | {it.get('category','-')} | {tags_disp}")
                    st.caption((it.get("content","") or "")[:300] + "...")

    with tabs[3]:
        st.subheader(tr("kb_settings_header"))
        st.caption("Optional dependencies: PyPDF2, python-docx, openpyxl.")
        missing = []
        try: import PyPDF2
        except: missing.append("PyPDF2")
        try: import docx
        except: missing.append("python-docx")
        try: import openpyxl
        except: missing.append("openpyxl")
        
        if missing:
            st.warning("Missing: " + ", ".join(missing))
        else:
            st.success("All dependencies installed.")


# ==================== 租户级 Telegram 登录组件 ====================
def render_tenant_login_panel(tenant_id, session_name):
    """支持多租户和多Session的登录面板"""
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError
    
    # 状态初始化
    state_key = f"login_state_{tenant_id}_{session_name}"
    if state_key not in st.session_state:
        st.session_state[state_key] = {"step": "phone", "phone": "", "code": "", "password": "", "message": ""}
    state = st.session_state[state_key]

    # 确定 Session 路径
    if not session_name.endswith(".session"):
        session_name += ".session"
    
    session_dir = f"data/tenants/{tenant_id}/sessions"
    os.makedirs(session_dir, exist_ok=True)
    session_path = os.path.join(session_dir, session_name)
    
    # 兼容 Default 租户
    if tenant_id == "default":
        # 如果是 default，尝试直接使用根目录，或者 data/tenants/default/sessions
        # 为保持一致性，建议 default 也走 sessions 目录，但为了兼容旧版：
        if not os.path.exists(session_dir):
            session_path = session_name # Root dir

    st.markdown(f"### 🔐 登录 Telegram: `{session_name}`")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        st.error("❌ 未配置 TELEGRAM_API_ID / API_HASH")
        return

    # 动态创建 Client
    # 注意：Telethon 在 Streamlit 中需要小心 Loop 管理
    # 这里我们使用一个临时的 loop 或者 sync context
    
    msg = state.get("message", "")
    if msg:
        if "成功" in msg:
            st.success(msg)
        else:
            st.warning(msg)

    phone = st.text_input("手机号码 (带区号, 如 +86...)", value=state.get("phone", ""), key=f"login_phone_{state_key}")
    state["phone"] = phone
    
    c1, c2 = st.columns(2)
    with c1:
        code = st.text_input("验证码", value=state.get("code", ""), key=f"login_code_{state_key}")
    with c2:
        password = st.text_input("两步验证密码 (如有)", value=state.get("password", ""), type="password", key=f"login_pwd_{state_key}")
        
    state["code"] = code
    state["password"] = password

    def get_client():
        # Telethon session path: 如果不带后缀，它会自动加 .session
        # 这里我们传递完整路径（不带后缀给 Telethon，因为它会自己加）
        s_path_no_ext = session_path[:-8] if session_path.endswith(".session") else session_path
        # 强制使用新的 Loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = TelegramClient(s_path_no_ext, int(api_id), api_hash, loop=loop)
        client.connect() # Sync wait
        return client, loop

    c_btn1, c_btn2 = st.columns(2)
    
    with c_btn1:
        if st.button("📡 发送验证码", key=f"btn_send_{state_key}"):
            if not phone:
                state["message"] = "请输入手机号"
            else:
                try:
                    client, loop = get_client()
                    with client:
                        client.send_code_request(phone)
                    state["step"] = "code"
                    state["message"] = "✅ 验证码已发送，请查收 Telegram"
                except Exception as e:
                    state["message"] = f"发送失败: {e}"
                st.rerun()

    with c_btn2:
        if st.button("🚀 登录", type="primary", key=f"btn_login_{state_key}"):
            try:
                client, loop = get_client()
                with client:
                    if state.get("step") == "password" or password:
                         client.sign_in(password=password)
                    else:
                         client.sign_in(phone=phone, code=code)
                    
                    if client.is_user_authorized():
                        me = client.get_me()
                        username = me.username or me.first_name
                        state["message"] = f"✅ 登录成功！用户: {username}"
                        st.session_state.show_login_panel = False
                        
                        # 尝试自动更新数据库中的用户名
                        acc_db_path = f"data/tenants/{tenant_id}/accounts.json"
                        if os.path.exists(acc_db_path):
                            try:
                                with open(acc_db_path, "r", encoding="utf-8") as f:
                                    acc_db = json.load(f)
                                for acc in acc_db.get("accounts", []):
                                    # 模糊匹配 session file
                                    if session_name in acc.get("session_file", ""):
                                        acc["username"] = username
                                        acc["status"] = "active"
                                        acc["note"] = "Web登录成功"
                                        break
                                with open(acc_db_path, "w", encoding="utf-8") as f:
                                    json.dump(acc_db, f, ensure_ascii=False, indent=2)
                            except: pass
                            
                    else:
                        state["message"] = "❌ 登录未完成，可能需要密码"
            except SessionPasswordNeededError:
                state["step"] = "password"
                state["message"] = "🔐 需要两步验证密码"
            except Exception as e:
                state["message"] = f"登录失败: {e}"
            st.rerun()

def render_telegram_panel():
    from admin import start_bot, stop_bot, get_bot_status
    st.header(f"📱 {tr('tg_panel_header')}")
    _render_scope_hint("仅 Telegram 平台生效")
    
    # 租户隔离上下文
    tenant_id = st.session_state.get('tenant', 'default')
    
    # --- 账号选择器 ---
    import json
    acc_db_path = f"data/tenants/{tenant_id}/accounts.json"
    tg_accounts = []
    if os.path.exists(acc_db_path):
        try:
            with open(acc_db_path, "r", encoding="utf-8") as f:
                acc_db = json.load(f)
            tg_accounts = [a for a in acc_db.get("accounts", []) if a.get("platform") == "Telegram"]
        except:
            pass
    
    selected_session_file = "userbot_session.session"
    selected_session_name = "userbot_session"
    selected_acc = None
    
    if tg_accounts:
        account_options = {}
        for a in tg_accounts:
            label = f"{a.get('username', '未命名')} ({a.get('session_file', 'No Session')})"
            account_options[label] = a
        c_sel, _ = st.columns([1, 2])
        with c_sel:
            selected_label = st.selectbox("👉 选择当前操作的 Telegram 账号", list(account_options.keys()), key="tg_panel_acc_sel")
        if selected_label:
            selected_acc = account_options[selected_label]
            if selected_acc.get("session_file"):
                selected_session_file = selected_acc["session_file"]
                if not selected_session_file.endswith(".session"): selected_session_file += ".session"
                selected_session_name = selected_session_file[:-8]
    else:
        st.info("💡 当前租户未添加 Telegram 账号，使用默认会话配置。")
    
    # 状态显示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 传递 tenant_id 获取状态
        is_running, pid = get_bot_status(tenant_id=tenant_id)
        if is_running:
            st.success(f"{tr('tg_status_running')} (PID: {pid})")
        else:
            st.error(tr('tg_status_stopped'))
    
    with col2:
        # 检查租户专属 Session (基于选择的账号)
        session_file_path = f"data/tenants/{tenant_id}/sessions/{selected_session_file}"
        if tenant_id == 'default' and not os.path.exists(session_file_path) and os.path.exists(selected_session_file):
             session_file_path = selected_session_file
             
        session_exists = os.path.exists(session_file_path) and os.path.getsize(session_file_path) > 0
        
        if session_exists:
            st.success(f"{tr('tg_status_logged_in')}\n({selected_session_file})")
            # 自动同步状态逻辑
            if selected_acc and selected_acc.get("status") != "active":
                try:
                    with open(acc_db_path, "r", encoding="utf-8") as f: fresh_db = json.load(f)
                    updated = False
                    for acc in fresh_db.get("accounts", []):
                        if acc.get("platform") == "Telegram" and acc.get("session_file") == selected_acc.get("session_file"):
                            if acc.get("status") != "active":
                                acc["status"] = "active"
                                if not acc.get("note") or acc.get("note") == "等待首次验证":
                                     acc["note"] = "系统自动激活 (Panel Check)"
                                acc["updated_at"] = datetime.now().isoformat()
                                updated = True
                            break
                    if updated:
                        with open(acc_db_path, "w", encoding="utf-8") as f:
                            json.dump(fresh_db, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Auto-update status failed: {e}")
        else:
            st.warning(f"{tr('tg_status_not_logged_in')}\n({selected_session_file})")
            if st.button("📲 去登录", key="tg_goto_login"):
                @st.dialog("Telegram 登录指南")
                def show_login_guide():
                    st.markdown(f"""
                    ### 🚀 登录配置: {selected_acc.get('username') if selected_acc else 'Default'}
                    1. 确保已配置 API ID/Hash。
                    2. 点击下方按钮开始登录。
                    Target: `{selected_session_file}`
                    """)
                    if st.button("开始登录操作", type="primary"):
                         st.session_state.show_login_panel = True
                         st.rerun()
                show_login_guide()

    with col3:
        config_path = f"data/tenants/{tenant_id}/platforms/telegram/config.txt"
        config_exists = os.path.exists(config_path) or (tenant_id == 'default' and os.path.exists("platforms/telegram/config.txt"))
        if config_exists:
            st.success(tr('tg_config_success'))
        else:
            st.error(tr('tg_config_missing'))
            if st.button("⚙️ 去配置", key="tg_goto_config"):
                st.info("请切换到下方【功能配置】页签进行保存。")
    
    st.divider()

    if st.session_state.get("show_login_panel"):
        with st.expander(tr("tg_login_header"), expanded=True):
            # 使用新版租户级登录面板，传递当前选中的 session
            render_tenant_login_panel(tenant_id, selected_session_name)
    
    # 控制按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(tr('tg_btn_start'), use_container_width=True, type="primary", 
                    disabled=is_running, key="tg_start"):
            # 传递 tenant_id 和 session_name 启动
            success, message = start_bot(tenant_id=tenant_id, session_name=selected_session_name)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button(tr('tg_btn_stop'), width="stretch", 
                    disabled=not is_running, key="tg_stop"):
            # 传递 tenant_id 停止
            success, message = stop_bot(tenant_id=tenant_id)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col3:
        if st.button(tr('tg_btn_restart'), width="stretch",
                    disabled=False, key="tg_restart"):
            # 传递 tenant_id 重启
            if is_running:
                stop_success, stop_msg = stop_bot(tenant_id=tenant_id)
                if not stop_success:
                    st.warning(f"停止失败: {stop_msg}")
                import time
                time.sleep(1)
            start_success, start_msg = start_bot(tenant_id=tenant_id, session_name=selected_session_name)
            if start_success:
                st.success(tr('tg_restart_success'))
                import time
                time.sleep(0.8)
                st.rerun()
            else:
                st.error(f"重启失败: {start_msg}")
    
    st.divider()
    
    # Tab 界面（使用 radio 避免按钮触发后回到默认页）
    tab_map = {
        tr("tg_tab_config"): render_telegram_config,
        tr("tg_tab_broadcast"): render_telegram_broadcast,
        tr("tg_tab_logs"): render_telegram_logs,
        tr("tg_tab_stats"): render_telegram_stats,
        tr("tg_tab_flow"): render_telegram_flow
    }
    panel_tabs = list(tab_map.keys())
    
    active_tab = st.radio(
        "telegram_tabs",
        panel_tabs,
        horizontal=True,
        label_visibility="collapsed",
        key="tg_panel_tab"
    )

    if active_tab in tab_map:
        tab_map[active_tab]()

def render_telegram_config():
    """Telegram 配置界面（支持租户隔离）"""
    # 辅助函数：根据租户上下文读写文件
    tenant_id = st.session_state.get('tenant', 'default')
    
    def get_tenant_path(rel_path):
        # 优先使用租户目录
        return f"data/tenants/{tenant_id}/{rel_path}"

    def read_tenant_file(rel_path, default=""):
        # 1. 尝试租户目录
        path = get_tenant_path(rel_path)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                pass
        
        # 2. 如果是 default 租户，尝试根目录下的旧路径（兼容性）
        if tenant_id == 'default':
            if os.path.exists(rel_path):
                try:
                    with open(rel_path, "r", encoding="utf-8") as f:
                        return f.read()
                except:
                    pass
        
        # 3. 如果文件不存在，返回默认值
        return default

    def write_tenant_file(rel_path, content):
        path = get_tenant_path(rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, "Success"
        except Exception as e:
            return False, str(e)
            
    st.subheader(tr("tg_config_header"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(tr("tg_cfg_persona"))
        # 使用相对路径 platforms/telegram/prompt.txt
        prompt = st.text_area(
            tr("tg_cfg_prompt_label"),
            value=read_tenant_file("platforms/telegram/prompt.txt"),
            height=200,
            key="tg_prompt"
        )
        if st.button(tr("tg_cfg_save_prompt"), key="save_prompt"):
            write_tenant_file("platforms/telegram/prompt.txt", prompt)
            log_admin_op("tg_prompt_save", {"tenant": tenant_id})
            st.success(tr("common_success"))
    
    with col2:
        st.markdown(tr("tg_cfg_keywords"))
        keywords = st.text_area(
            tr("tg_cfg_keywords_placeholder"),
            value=read_tenant_file("platforms/telegram/keywords.txt", "帮我\n求助\nAI"),
            height=200,
            key="tg_keywords"
        )
        if st.button(tr("tg_cfg_save_keywords"), key="save_keywords"):
            write_tenant_file("platforms/telegram/keywords.txt", keywords)
            log_admin_op("tg_keywords_save", {"tenant": tenant_id})
            st.success(tr("common_success"))
    
    st.divider()

    st.markdown(tr("tg_cfg_qa"))
    qa_content = read_tenant_file("platforms/telegram/qa.txt", "")
    qa_text = st.text_area(
        tr("tg_cfg_qa_placeholder"),
        value=qa_content,
        height=220,
        key="tg_qa_text"
    )
    if st.button(tr("tg_cfg_save_qa"), key="save_tg_qa"):
        success, message = write_tenant_file("platforms/telegram/qa.txt", qa_text)
        if success:
            # 自动触发知识库刷新：需要更新 config.txt 中的标志位
            try:
                cfg_content = read_tenant_file("platforms/telegram/config.txt", "")
                lines = []
                kb_refresh_found = False
                for line in cfg_content.splitlines():
                    if line.strip().startswith("KB_REFRESH="):
                        lines.append("KB_REFRESH=on")
                        kb_refresh_found = True
                    else:
                        lines.append(line)
                
                if not kb_refresh_found:
                    lines.append("KB_REFRESH=on")

                write_tenant_file("platforms/telegram/config.txt", "\n".join(lines))
                st.info("✅ 已设置自动刷新标志，机器人将在下一次交互时重建知识库")
            except Exception as e:
                st.warning(f"无法设置自动刷新: {e}")

            log_admin_op("tg_qa_save", {"tenant": tenant_id})
            st.success(tr("common_success"))
        else:
            st.error(f"{tr('common_error')}: {message}")

    st.divider()
    
    # 功能开关与参数
    st.markdown(tr("tg_cfg_switches"))
    config_content = read_tenant_file("platforms/telegram/config.txt", "PRIVATE_REPLY=on\nGROUP_REPLY=on")
    
    current_config = {
        'PRIVATE_REPLY': True, 
        'GROUP_REPLY': True, 
        'CONV_ORCHESTRATION': False,
        'CONVERSATION_MODE': 'ai_visible',
        'AI_TEMPERATURE': 0.7,
        'AUDIT_ENABLED': True,
        'AUDIT_MAX_RETRIES': 3,
        'AUDIT_TEMPERATURE': 0.0,
        'AUDIT_MODE': 'local',
        'AUDIT_SERVERS': 'http://127.0.0.1:8000',
        'AUTO_QUOTE': False,
        'QUOTE_INTERVAL_SECONDS': 30.0,
        'QUOTE_MAX_LEN': 200,
        'KB_ONLY_REPLY': False,
        'HANDOFF_KEYWORDS': '',
        'HANDOFF_MESSAGE': '',
        'KB_FALLBACK_MESSAGE': ''
    }
    for line in config_content.split('\n'):
        if '=' in line and not line.strip().startswith('#'):
            parts = line.split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                raw_value = parts[1].strip()
                value = raw_value.lower()
                
                if key in ['PRIVATE_REPLY', 'GROUP_REPLY', 'AUDIT_ENABLED', 'AUTO_QUOTE', 'CONV_ORCHESTRATION', 'KB_ONLY_REPLY']:
                    current_config[key] = (value == 'on')
                elif key == 'AI_TEMPERATURE':
                    try: current_config[key] = float(value)
                    except: pass
                elif key == 'AUDIT_TEMPERATURE':
                    try: current_config[key] = float(value)
                    except: pass
                elif key == 'AUDIT_MAX_RETRIES':
                    try: current_config[key] = int(value)
                    except: pass
                elif key == 'AUDIT_MODE':
                    current_config[key] = value
                elif key == 'AUDIT_SERVERS':
                    current_config[key] = raw_value
                elif key == 'CONVERSATION_MODE':
                    current_config[key] = value
                elif key == 'QUOTE_INTERVAL_SECONDS':
                    try: current_config[key] = float(value)
                    except: pass
                elif key == 'QUOTE_MAX_LEN':
                    try: current_config[key] = int(value)
                    except: pass
                elif key == 'HANDOFF_KEYWORDS':
                    current_config[key] = raw_value
                elif key == 'HANDOFF_MESSAGE':
                    current_config[key] = raw_value
                elif key == 'KB_FALLBACK_MESSAGE':
                    current_config[key] = raw_value
    
    col1, col2 = st.columns(2)
    
    with col1:
        private_reply = st.toggle(
            tr("tg_cfg_private_reply"),
            value=current_config['PRIVATE_REPLY'],
            key="tg_private"
        )
        
        # Orchestration Switch
        orchestration_enabled = st.toggle(
            "🧠 AI 剧本引擎 (Orchestration Engine)",
            value=current_config['CONV_ORCHESTRATION'],
            help="启用后，系统将按照 Stage/Persona/KB 流程进行AI剧本配置执行 (Supervisor -> Stage Agent)",
            key="tg_orchestration"
        )
        
        kb_only_reply = st.toggle(
            "📚 知识库直答（不走剧本）",
            value=current_config['KB_ONLY_REPLY'],
            help="开启后，回复将直接引用知识库内容，不调用AI与人设剧本",
            key="tg_kb_only_reply"
        )
    
    with col2:
        group_reply = st.toggle(
            tr("tg_cfg_group_reply"),
            value=current_config['GROUP_REPLY'],
            key="tg_group"
        )
        st.markdown(tr("tg_cfg_conv_mode"))
        conv_options = [tr("tg_cfg_conv_ai"), tr("tg_cfg_conv_human")]
        mode_idx = 0 if current_config.get('CONVERSATION_MODE','ai_visible') == 'ai_visible' else 1
        conv_choice = st.radio(
            tr("tg_cfg_conv_mode"),
            conv_options,
            index=mode_idx,
            horizontal=True,
            key="tg_conv_mode"
        )
        conv_value = 'ai_visible' if conv_choice == tr("tg_cfg_conv_ai") else 'human_simulated'
    
    st.divider()
    st.markdown("🛠️ 兜底与人工配置")
    hk_col1, hk_col2 = st.columns([1,1])
    with hk_col1:
        handoff_keywords = st.text_input("人工触发关键词（逗号分隔）", value=current_config.get('HANDOFF_KEYWORDS',''), key="tg_handoff_keywords")
    with hk_col2:
        handoff_message = st.text_input("人工兜底话术（单行）", value=current_config.get('HANDOFF_MESSAGE',''), key="tg_handoff_message")
    kb_fallback_message = st.text_input("KB_ONLY兜底话术（单行）", value=current_config.get('KB_FALLBACK_MESSAGE',''), key="tg_kb_fallback_message")
    
    st.divider()
    st.markdown(tr("tg_cfg_quote"))
    qcol1, qcol2, qcol3 = st.columns([1, 1, 1])
    with qcol1:
        auto_quote = st.toggle(tr("tg_cfg_auto_quote"), value=current_config['AUTO_QUOTE'], key="tg_auto_quote")
    with qcol2:
        quote_interval = st.number_input(tr("tg_cfg_quote_interval"), min_value=5.0, max_value=120.0, value=float(current_config['QUOTE_INTERVAL_SECONDS']), step=5.0, key="tg_quote_interval")
    with qcol3:
        quote_max_len = st.number_input(tr("tg_cfg_quote_len"), min_value=50, max_value=500, value=int(current_config['QUOTE_MAX_LEN']), step=10, key="tg_quote_max_len")
    
    st.divider()

    # AI 温度配置
    st.markdown(tr("tg_cfg_temp"))
    
    temp_col1, temp_col2 = st.columns([2, 1])
    
    with temp_col1:
        ai_temperature = st.slider(
            tr("tg_cfg_temp_label"),
            min_value=0.0,
            max_value=1.0,
            value=current_config['AI_TEMPERATURE'],
            step=0.1,
            key="tg_temp_slider"
        )
        st.caption(f"Value: **{ai_temperature:.1f}**")
    
    with temp_col2:
        st.info("""
        **Info:**
        - **0.0**: Precise
        - **0.5**: Balanced
        - **1.0**: Creative
        """)
    
    st.divider()
    st.markdown(tr("tg_cfg_audit"))
    
    audit_col1, audit_col2 = st.columns(2)
    with audit_col1:
        audit_enabled = st.toggle(tr("tg_cfg_audit_enable"), value=current_config['AUDIT_ENABLED'], key="tg_audit_enabled")
        
        # 审核模式选择
        mode_idx = 0
        if current_config['AUDIT_MODE'] == 'dual':
            mode_idx = 1
        elif current_config['AUDIT_MODE'] == 'remote':
            mode_idx = 2
        audit_mode = st.radio(
            tr("tg_cfg_audit_mode"), 
            ["local", "dual", "remote"], 
            index=mode_idx, 
            key="tg_audit_mode", 
            horizontal=True
        )
        
    with audit_col2:
        audit_max_retries = st.number_input(tr("tg_cfg_audit_retries"), min_value=1, max_value=5, value=current_config['AUDIT_MAX_RETRIES'], key="tg_audit_retries")
        audit_temperature = st.slider(tr("tg_cfg_audit_strictness"), 0.0, 1.0, current_config['AUDIT_TEMPERATURE'], 0.1, key="tg_audit_temp")
        st.caption("Rec: 0.0")
        guide_strength = st.slider(tr("tg_cfg_audit_guide"), 0.0, 1.0, float(current_config.get('AUDIT_GUIDE_STRENGTH', 0.7)), 0.1, key="tg_audit_guide_strength")

    # 临时关闭审核与恢复按钮 (略微简化逻辑以适配租户文件读写)
    col_tmp1, col_tmp2 = st.columns(2)
    with col_tmp1:
        if st.button(tr("tg_cfg_audit_temp_off"), key="tg_audit_temp_off", width="stretch"):
            st.session_state['audit_prev_enabled'] = audit_enabled
            import time as _time
            st.session_state['audit_temp_disable_until'] = _time.time() + 300
            
            # 使用租户文件写入
            saved_cfg = read_tenant_file("platforms/telegram/config.txt", "")
            lines = []
            for line in saved_cfg.splitlines():
                if line.strip().startswith("AUDIT_ENABLED="):
                    lines.append("AUDIT_ENABLED=off")
                else:
                    lines.append(line)
            write_tenant_file("platforms/telegram/config.txt", "\n".join(lines))
            st.success(tr("common_success"))
            
    with col_tmp2:
        if st.button(tr("tg_cfg_audit_restore"), key="tg_audit_restore", width="stretch"):
            prev = st.session_state.get('audit_prev_enabled', True)
            saved_cfg = read_tenant_file("platforms/telegram/config.txt", "")
            lines = []
            for line in saved_cfg.splitlines():
                if line.strip().startswith("AUDIT_ENABLED="):
                    lines.append(f"AUDIT_ENABLED={'on' if prev else 'off'}")
                else:
                    lines.append(line)
            write_tenant_file("platforms/telegram/config.txt", "\n".join(lines))
            st.success(tr("common_success"))

    # 远程服务器配置 (仅在 remote 模式下显示或生效)
    audit_servers = current_config['AUDIT_SERVERS']
    if audit_mode in ('remote', 'dual'):
        audit_servers = st.text_input(
            tr("tg_cfg_audit_servers"), 
            value=current_config['AUDIT_SERVERS'], 
            key="tg_audit_servers"
        )

    if st.button(tr("tg_cfg_save_all"), width="stretch"):
        new_config = f"""# ========================================
# Telegram AI Bot - 功能配置
# ========================================

# 个人消息回复开关
PRIVATE_REPLY={'on' if private_reply else 'off'}

# 群消息回复开关
GROUP_REPLY={'on' if group_reply else 'off'}

# AI 剧本引擎 (SOP/Persona/KB)
CONV_ORCHESTRATION={'on' if orchestration_enabled else 'off'}

# 知识库直答（不走剧本）
KB_ONLY_REPLY={'on' if kb_only_reply else 'off'}

# 对话呈现模式
CONVERSATION_MODE={conv_value}

# 人工触发关键词（逗号分隔）
HANDOFF_KEYWORDS={handoff_keywords}

# 人工兜底话术（单行）
HANDOFF_MESSAGE={handoff_message}

# KB_ONLY兜底话术（单行）
KB_FALLBACK_MESSAGE={kb_fallback_message}

# AI 温度 (0.0-1.0)
AI_TEMPERATURE={ai_temperature:.1f}

# 自动引用
AUTO_QUOTE={'on' if auto_quote else 'off'}
QUOTE_INTERVAL_SECONDS={float(quote_interval):.1f}
QUOTE_MAX_LEN={int(quote_max_len)}

# ----------------------------------------
# 内容审核配置 (双机拦截)
# ----------------------------------------
AUDIT_ENABLED={'on' if audit_enabled else 'off'}
AUDIT_MODE={audit_mode}
AUDIT_SERVERS={audit_servers}
AUDIT_MAX_RETRIES={audit_max_retries}
AUDIT_TEMPERATURE={audit_temperature:.1f}
AUDIT_GUIDE_STRENGTH={guide_strength:.1f}
"""
        write_tenant_file("platforms/telegram/config.txt", new_config)
        log_admin_op("tg_config_save", {"tenant": tenant_id, "AUTO_QUOTE": auto_quote})
        st.success(tr("common_success"))


    st.markdown(tr("tg_cfg_audit_kw"))
    from keyword_manager import KeywordManager
    km = KeywordManager()
    role_kw = st.session_state.get('user_role', 'SuperAdmin')
    can_edit_kw = (role_kw == 'Auditor' or role_kw == 'SuperAdmin')
    kwc1, kwc2 = st.columns(2)
    with kwc1:
        st.markdown(tr("tg_kw_block"))
        blk = km.get_keywords().get('block', [])
        st.write(f"Count: {len(blk)}")
        if can_edit_kw:
            new_blk = st.text_input(tr("tg_kw_add"), key="tg_kw_add_block")
            if st.button(tr("tg_kw_add"), key="tg_kw_add_block_btn"):
                if new_blk:
                    ok, msg = km.add_keyword('block', new_blk)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            if blk:
                del_blk = st.selectbox(tr("tg_kw_del"), [""] + blk, key="tg_kw_del_block")
                if st.button(tr("tg_kw_del"), key="tg_kw_del_block_btn"):
                    if del_blk:
                        km.remove_keyword('block', del_blk)
                        st.success(f"Deleted {del_blk}")
                        st.rerun()
                rn_blk_col1, rn_blk_col2 = st.columns([1,1])
                with rn_blk_col1:
                    rn_blk_sel = st.selectbox(tr("tg_kw_rename"), [""] + blk, key="tg_kw_rename_block_sel")
                with rn_blk_col2:
                    rn_blk_new = st.text_input(tr("tg_kw_new_name"), key="tg_kw_rename_block_new")
                if st.button(tr("tg_kw_rename"), key="tg_kw_rename_block_btn"):
                    if rn_blk_sel and rn_blk_new:
                        ok, msg = km.rename_keyword('block', rn_blk_sel, rn_blk_new)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
        else:
            st.info("Auditor Only")
        st.markdown(" ".join([f"`{k}`" for k in blk]))
    with kwc2:
        st.markdown(tr("tg_kw_sensitive"))
        sen = km.get_keywords().get('sensitive', [])
        st.write(f"Count: {len(sen)}")
        if can_edit_kw:
            new_sen = st.text_input(tr("tg_kw_add"), key="tg_kw_add_sens")
            if st.button(tr("tg_kw_add"), key="tg_kw_add_sens_btn"):
                if new_sen:
                    ok, msg = km.add_keyword('sensitive', new_sen)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            if sen:
                del_sen = st.selectbox(tr("tg_kw_del"), [""] + sen, key="tg_kw_del_sens")
                if st.button(tr("tg_kw_del"), key="tg_kw_del_sens_btn"):
                    if del_sen:
                        km.remove_keyword('sensitive', del_sen)
                        st.success(f"Deleted {del_sen}")
                        st.rerun()
                rn_sen_col1, rn_sen_col2 = st.columns([1,1])
                with rn_sen_col1:
                    rn_sen_sel = st.selectbox(tr("tg_kw_rename"), [""] + sen, key="tg_kw_rename_sens_sel")
                with rn_sen_col2:
                    rn_sen_new = st.text_input(tr("tg_kw_new_name"), key="tg_kw_rename_sens_new")
                if st.button(tr("tg_kw_rename"), key="tg_kw_rename_sens_btn"):
                    if rn_sen_sel and rn_sen_new:
                        ok, msg = km.rename_keyword('sensitive', rn_sen_sel, rn_sen_new)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
        else:
            st.info("Auditor Only")
        st.markdown(" ".join([f"`{k}`" for k in sen]))
    st.divider()
    st.markdown(tr("tg_kw_allow"))
    alw = km.get_keywords().get('allow', [])
    st.write(f"Count: {len(alw)}")
    if can_edit_kw:
        new_alw = st.text_input(tr("tg_kw_add"), key="tg_kw_add_allow")
        if st.button(tr("tg_kw_add"), key="tg_kw_add_allow_btn"):
            if new_alw:
                ok, msg = km.add_keyword('allow', new_alw)
                if ok: st.success(msg)
                else: st.warning(msg)
                st.rerun()
        if alw:
            del_alw = st.selectbox(tr("tg_kw_del"), [""] + alw, key="tg_kw_del_allow")
            if st.button(tr("tg_kw_del"), key="tg_kw_del_allow_btn"):
                if del_alw:
                    km.remove_keyword('allow', del_alw)
                    st.success(f"Deleted {del_alw}")
                    st.rerun()
            rn_alw_col1, rn_alw_col2 = st.columns([1,1])
            with rn_alw_col1:
                rn_alw_sel = st.selectbox(tr("tg_kw_rename"), [""] + alw, key="tg_kw_rename_allow_sel")
            with rn_alw_col2:
                rn_alw_new = st.text_input(tr("tg_kw_new_name"), key="tg_kw_rename_allow_new")
            if st.button(tr("tg_kw_rename"), key="tg_kw_rename_allow_btn"):
                if rn_alw_sel and rn_alw_new:
                    ok, msg = km.rename_keyword('allow', rn_alw_sel, rn_alw_new)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
    else:
        st.info("Auditor Only")
    st.markdown(" ".join([f"`{k}`" for k in alw]))

    st.markdown(tr("tg_kw_fallback"))
    fallback_path = "platforms/telegram/audit_fallback.txt"
    fallback_text = st.text_area(
        tr("tg_kw_fallback"),
        value=read_tenant_file(fallback_path, ""),
        height=160,
        key="tg_audit_fallback"
    )
    if st.button(tr("tg_kw_save_fallback"), key="save_audit_fallback", width="stretch"):
        write_tenant_file(fallback_path, fallback_text)
        log_admin_op("tg_fallback_save", {"tenant": tenant_id, "path": fallback_path})
        st.success(tr("common_success"))

    st.markdown(tr("tg_kw_clean_qa"))
    qa_path = "platforms/telegram/qa.txt"
    if st.button(tr("tg_kw_clean_btn"), key="tg_qa_clean", width="stretch"):
        raw = read_tenant_file(qa_path, "")
        lines = raw.splitlines()
        keywords = ["政策", "方案", "办理", "签证", "移民", "B-1", "B-5", "参谋", "顾问", "推广", "营销"]
        cleaned = []
        removed = 0
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            if len(s) > 400 and any(k in s for k in keywords):
                removed += 1
                continue
            cleaned.append(s)
        write_tenant_file(qa_path, "\n".join(cleaned))
        log_admin_op("tg_qa_clean", {"tenant": tenant_id, "removed": removed})
        st.success(f"{tr('common_success')}, Removed {removed} items")

    st.divider()

    st.subheader(tr("tg_whitelist_header"))
    groups = load_tg_group_cache()
    if not groups:
        st.info("No group cache found. Run bot first.")
        return

    selected_ids = load_tg_selected_group_ids()
    options = [format_group_label(item) for item in groups]
    label_to_id = {format_group_label(item): item["id"] for item in groups}
    default_labels = [label for label in options if label_to_id.get(label) in selected_ids]

    selected_labels = st.multiselect(
        tr("tg_whitelist_select"),
        options,
        default=default_labels,
        key="tg_whitelist_select"
    )
    if st.button(tr("tg_whitelist_save"), key="save_tg_whitelist", width="stretch"):
        save_tg_selected_group_ids([label_to_id[label] for label in selected_labels])
        log_admin_op("tg_whitelist_save", {"count": len(selected_labels)})
        st.success(tr("common_success"))

# ==================== 租户级工具函数 ====================
def _get_tenant_tg_paths(tenant_id):
    """获取租户 Telegram 相关路径"""
    base = f"data/tenants/{tenant_id}/platforms/telegram"
    return {
        "group_cache": os.path.join(base, "group_cache.json"),
        "selected_groups": os.path.join(base, "selected_groups.json"),
        "logs_dir": os.path.join(base, "logs"),
        "broadcast_log": os.path.join(base, "logs", "broadcast.log")
    }

def load_tg_group_cache_tenant(tenant_id):
    path = _get_tenant_tg_paths(tenant_id)["group_cache"]
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Convert dict to list
            if isinstance(data, dict):
                return [{"id": k, **v} for k, v in data.items()]
            return data
        except:
            return []
    # 兼容旧路径
    if tenant_id == "default" and os.path.exists("platforms/telegram/group_cache.json"):
        try:
            with open("platforms/telegram/group_cache.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return [{"id": k, **v} for k, v in data.items()]
        except: pass
    return []

def load_tg_selected_group_ids_tenant(tenant_id):
    path = _get_tenant_tg_paths(tenant_id)["selected_groups"]
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return set(json.load(f).get("selected_ids", []))
        except:
            return set()
    # 兼容旧路径
    if tenant_id == "default" and os.path.exists("platforms/telegram/selected_groups.json"):
        try:
            with open("platforms/telegram/selected_groups.json", "r", encoding="utf-8") as f:
                return set(json.load(f).get("selected_ids", []))
        except: pass
    return set()

def save_tg_selected_group_ids_tenant(tenant_id, ids):
    path = _get_tenant_tg_paths(tenant_id)["selected_groups"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"selected_ids": list(ids)}, f)

def render_telegram_broadcast():
    """Telegram 群发界面 (多租户适配版)"""
    st.subheader(tr("tg_bc_header"))
    st.warning(tr("tg_bc_warn"))

    tenant_id = st.session_state.get('tenant', 'default')
    
    # --- 账号选择器 ---
    # 逻辑与 Panel 类似，但这里只选择用于发送的 Session
    import json
    acc_db_path = f"data/tenants/{tenant_id}/accounts.json"
    tg_accounts = []
    if os.path.exists(acc_db_path):
        try:
            with open(acc_db_path, "r", encoding="utf-8") as f:
                acc_db = json.load(f)
            tg_accounts = [a for a in acc_db.get("accounts", []) if a.get("platform") == "Telegram"]
        except: pass
    
    selected_session_file = "userbot_session.session"
    # 如果有多个账号，提供选择
    if tg_accounts:
        account_options = {}
        for a in tg_accounts:
            label = f"{a.get('username', '未命名')} ({a.get('session_file', 'No Session')})"
            account_options[label] = a
        c_sel, _ = st.columns([1, 2])
        with c_sel:
            sel_label = st.selectbox("👉 选择发送账号", list(account_options.keys()), key="tg_bc_acc_sel")
            if sel_label:
                s_file = account_options[sel_label].get("session_file")
                if s_file: selected_session_file = s_file

    groups = load_tg_group_cache_tenant(tenant_id)
    if not groups:
        st.info(tr("tg_bc_no_cache"))
        return

    selected_ids = load_tg_selected_group_ids_tenant(tenant_id)
    mode_keys = ["tg_bc_mode_whitelist", "tg_bc_mode_non_whitelist", "tg_bc_mode_all"]
    mode = st.radio(
        tr("tg_bc_mode"),
        mode_keys,
        format_func=tr,
        horizontal=True,
        key="tg_broadcast_mode"
    )

    if st.button(tr("tg_bc_load_btn"), key="tg_load_groups", use_container_width=True):
        if mode == "tg_bc_mode_whitelist":
            filtered = [g for g in groups if g["id"] in selected_ids]
        elif mode == "tg_bc_mode_non_whitelist":
            filtered = [g for g in groups if g["id"] not in selected_ids]
        else:
            filtered = groups
        st.session_state.tg_broadcast_groups = filtered
        st.session_state.tg_broadcast_selected = [format_group_label(g) for g in filtered]
        st.rerun()

    loaded_groups = st.session_state.get("tg_broadcast_groups", [])
    if not loaded_groups:
        st.info(tr("tg_bc_no_cache"))
        st.info(tr("tg_bc_tip_load"))
        return

    options = [format_group_label(item) for item in loaded_groups]
    label_to_id = {format_group_label(item): item["id"] for item in loaded_groups}

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button(tr("tg_bc_select_all"), key="tg_select_all", width="stretch"):
            st.session_state.tg_broadcast_selected = list(options)
            st.rerun()
    with col_b:
        if st.button(tr("tg_bc_select_none"), key="tg_select_none", width="stretch"):
            st.session_state.tg_broadcast_selected = []
            st.rerun()
    with col_c:
        if st.button(tr("tg_bc_select_invert"), key="tg_select_invert", width="stretch"):
            current = set(st.session_state.get("tg_broadcast_selected", []))
            st.session_state.tg_broadcast_selected = [x for x in options if x not in current]
            st.rerun()

    multiselect_kwargs = {"options": options, "key": "tg_broadcast_selected"}
    if "tg_broadcast_selected" not in st.session_state:
        multiselect_kwargs["default"] = st.session_state.get("tg_broadcast_selected", [])
    selected_labels = st.multiselect(tr("tg_bc_select_label"), **multiselect_kwargs)
    selected_chat_ids = [label_to_id[label] for label in selected_labels]

    interval_seconds = st.number_input(
        tr("tg_bc_interval"),
        min_value=0.0,
        value=3.0,
        step=0.5,
        key="tg_broadcast_interval"
    )
    message = st.text_area(
        tr("tg_broadcast_input_label"),
        placeholder=tr("tg_bc_msg_placeholder"),
        height=160,
        key="tg_broadcast_message"
    )

    if st.button(tr("tg_bc_send_btn"), type="primary", use_container_width=True, key="tg_broadcast_send"):
        if not selected_chat_ids:
            st.error(tr("tg_bc_err_no_group"))
        elif not message.strip():
            st.error(tr("tg_bc_err_no_content"))
        else:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def update_progress(current, total, label):
                progress_bar.progress(current / total)
                status_text.text(f"[{current}/{total}] -> {label}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 动态构建 Client (使用选定的 Session)
                # 这里我们稍微 hack 一下，直接在 send_broadcast 逻辑里传入 session_path
                # 但 admin.py 的 send_broadcast_ids_with_interval 默认是用全局 Client 还是？
                # 检查 admin.py 的实现，它应该是接受 client 参数或者自己创建。
                # 由于我们无法直接修改 admin.py 的函数签名（为了安全），我们在这里手动创建 client 并传递给它（如果它支持）。
                # 如果它不支持，我们必须在这里重写发送逻辑。
                # 假设它不支持，我们直接重写核心发送循环。
                
                from telethon import TelegramClient
                
                s_dir = f"data/tenants/{tenant_id}/sessions"
                if not os.path.exists(s_dir) and tenant_id == 'default': s_dir = "."
                s_path = os.path.join(s_dir, selected_session_file)
                if s_path.endswith(".session"): s_path = s_path[:-8]
                
                api_id = os.getenv("TELEGRAM_API_ID")
                api_hash = os.getenv("TELEGRAM_API_HASH")
                
                client = TelegramClient(s_path, int(api_id), api_hash, loop=loop)
                
                async def _broadcast_task():
                    await client.connect()
                    if not await client.is_user_authorized():
                        return [], 0, 0, "Client not authorized"
                    
                    recs = []
                    suc = 0
                    fail = 0
                    total = len(selected_chat_ids)
                    
                    for idx, cid in enumerate(selected_chat_ids):
                        # 获取群名
                        title = str(cid)
                        for g in loaded_groups:
                            if g["id"] == cid:
                                title = g["title"]
                                break
                        
                        try:
                            await client.send_message(int(cid), message)
                            recs.append(f"SUCCESS -> {title} ({cid})")
                            suc += 1
                        except Exception as e:
                            recs.append(f"FAILED -> {title} ({cid}): {e}")
                            fail += 1
                        
                        update_progress(idx + 1, total, title)
                        await asyncio.sleep(interval_seconds)
                    
                    await client.disconnect()
                    return recs, suc, fail, None

                records, success, failed, err = loop.run_until_complete(_broadcast_task())
                
                if err:
                    st.error(tr("tg_bc_fail_prefix").format(err))
                else:
                    st.success(tr("tg_bc_success_fmt").format(success, failed))
                
                # Append to persistent log (Tenant isolated)
                log_file = _get_tenant_tg_paths(tenant_id)["broadcast_log"]
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                with open(log_file, "a", encoding="utf-8") as f:
                    for rec in records:
                        f.write(f"[{format_time(datetime.now())}] {rec}\n")
            except Exception as e:
                st.error(f"Execution error: {e}")
            finally:
                loop.close()

    st.divider()
    st.subheader(tr("tg_bc_records"))
    log_file = _get_tenant_tg_paths(tenant_id)["broadcast_log"]
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            st.text_area("Logs", value="".join(lines[-50:]), height=200, label_visibility="collapsed")
        if st.button(tr("tg_bc_clear"), key="clear_bc_logs"):
            open(log_file, "w").close()
            st.success(tr("tg_log_cleared"))
            st.rerun()
    else:
        st.info(tr("tg_bc_no_records"))

def render_telegram_logs():
    """Telegram 日志界面 (多租户适配版)"""
    st.subheader(tr("tg_log_header"))
    st.caption(tr("tg_logs_subtitle"))

    tenant_id = st.session_state.get('tenant', 'default')
    paths = _get_tenant_tg_paths(tenant_id)
    
    # 兼容 Default 的旧日志路径
    if tenant_id == "default" and not os.path.exists(paths["logs_dir"]):
         # Fallback to platforms/telegram/logs
         sys_log = "platforms/telegram/logs/system.log"
         priv_log = "platforms/telegram/logs/private_chat.log"
         grp_log = "platforms/telegram/logs/group_chat.log"
         audit_log = "platforms/telegram/logs/audit.log"
    else:
         sys_log = os.path.join(paths["logs_dir"], "system.log")
         priv_log = os.path.join(paths["logs_dir"], "private_chat.log")
         grp_log = os.path.join(paths["logs_dir"], "group_chat.log")
         audit_log = os.path.join(paths["logs_dir"], "audit.log")

    log_tab1, log_tab2, log_tab3, log_tab4 = st.tabs([
        tr("tg_log_sys"), 
        tr("tg_log_priv"), 
        tr("tg_log_grp"), 
        tr("tg_log_audit")
    ])

    def render_log_tab(tab_label, file_path, key_prefix):
        if f"{key_prefix}_content" not in st.session_state:
            st.session_state[f"{key_prefix}_content"] = read_log_file(file_path)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button(tr("tg_log_load"), use_container_width=True, key=f"{key_prefix}_load"):
                st.session_state[f"{key_prefix}_content"] = read_log_file(file_path)
        with col2:
            if st.button(tr("tg_log_refresh"), use_container_width=True, key=f"{key_prefix}_refresh"):
                st.session_state[f"{key_prefix}_content"] = read_log_file(file_path)
        with col3:
            if st.button(tr("tg_log_clear"), use_container_width=True, key=f"{key_prefix}_clear"):
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    open(file_path, 'w').close()
                    st.session_state[f"{key_prefix}_content"] = ""
                    st.success(tr("tg_log_cleared"))
                except Exception as exc:
                    st.error(tr("tg_log_clear_fail").format(exc))

        logs = st.session_state.get(f"{key_prefix}_content", "")
        if not logs:
            st.info(tr("tg_log_tip_load"))
        st.text_area(tab_label, value=logs, height=360, disabled=True, key=f"{key_prefix}_text")

    with log_tab1:
        render_log_tab(tr("tg_log_sys"), sys_log, "tg_log_system")
    with log_tab2:
        render_log_tab(tr("tg_log_priv"), priv_log, "tg_log_private")
    with log_tab3:
        render_log_tab(tr("tg_log_grp"), grp_log, "tg_log_group")
    with log_tab4:
        render_log_tab(tr("tg_log_audit"), audit_log, "tg_log_audit")

def render_telegram_flow():
    st.subheader(tr("tg_flow_header"))
    st.markdown(tr("tg_flow_entry"))
    st.markdown(tr("tg_flow_trigger"))
    st.markdown("---")
    st.markdown(tr("tg_flow_branch_a"))
    st.markdown(tr("tg_flow_branch_a_1"))
    st.markdown(tr("tg_flow_branch_a_2"))
    st.markdown(tr("tg_flow_branch_a_3"))
    st.markdown("---")
    st.markdown(tr("tg_flow_branch_b"))
    st.markdown(tr("tg_flow_branch_b_1"))
    st.markdown(tr("tg_flow_branch_b_2"))
    st.markdown(tr("tg_flow_branch_b_3"))
    st.markdown(tr("tg_flow_branch_b_4"))
    st.markdown(tr("tg_flow_branch_b_5"))
    st.markdown(tr("tg_flow_branch_b_6"))
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(tr("tg_flow_kw_prio"))
        st.markdown(tr("tg_flow_kw_prio_1"))
        st.markdown(tr("tg_flow_kw_prio_2"))
        st.markdown(tr("tg_flow_kw_prio_3"))
    with col2:
        st.markdown(tr("tg_flow_fallback"))
        st.markdown(tr("tg_flow_fallback_1"))
        st.markdown(tr("tg_flow_fallback_2"))
    st.markdown("---")
    st.markdown(tr("tg_flow_files"))
    st.markdown(tr("tg_flow_files_1"))
    st.markdown(tr("tg_flow_files_2"))
    st.markdown(tr("tg_flow_files_3"))
    st.markdown(tr("tg_flow_files_4"))

def _ensure_data_dirs():
    base = os.path.join(BASE_DIR, "data")
    os.makedirs(base, exist_ok=True)
    os.makedirs(os.path.join(base, "config"), exist_ok=True)
    os.makedirs(os.path.join(base, "logs"), exist_ok=True)
    os.makedirs(os.path.join(base, "tenants"), exist_ok=True)
    return base

def log_admin_op(action, details):
    try:
        base = _ensure_data_dirs()
        log_file = os.path.join(base, "logs", "admin_ops.log")
        # 简单敏感字段掩码
        for k in ["api_key", "token", "secret"]:
            if k in details:
                details[k] = "***"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"action": action, "details": details, "ts": datetime.now().isoformat()}, ensure_ascii=False) + "\n")
        tenant_id = st.session_state.get("tenant", "default")
        role = st.session_state.get("user_role", "SuperAdmin")
        try:
            db.log_audit(tenant_id, role, action, details)
        except Exception:
            pass
    except Exception:
        pass

def render_accounts_panel():
    st.header(f"👥 {tr('acc_header')}")
    _render_scope_hint("当前租户全平台生效")
    base = _ensure_data_dirs()
    tenant = st.session_state.get("tenant", "default")
    tdir = os.path.join(base, "tenants", tenant)
    os.makedirs(tdir, exist_ok=True)
    db_path = os.path.join(tdir, "accounts.json")
    # Ensure sessions dir
    sessions_dir = os.path.join(tdir, "sessions")
    os.makedirs(sessions_dir, exist_ok=True)

    try:
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
        else:
            db = {"accounts": []}
    except Exception:
        db = {"accounts": []}
    
    st.caption(tr("acc_tenant").format(tenant))
    st.markdown(tr("acc_subtitle"))

    tabs = st.tabs(["📝 手动添加", "📂 批量导入 (Session)", "📋 账号列表"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            platform = st.selectbox(tr("acc_col_platform"), ["WeChat", "Weibo", "Twitter", "Telegram", "WhatsApp"], key="acc_platform")
            username = st.text_input(tr("acc_col_username"), key="acc_username")
            group = st.text_input(tr("acc_col_group"), key="acc_group")
        with col2:
            tags = st.text_input(tr("acc_col_tags"), key="acc_tags")
            refresh = st.number_input(tr("acc_col_refresh"), min_value=5, max_value=1440, value=60, step=5, key="acc_refresh")
        
        if st.button(tr("acc_btn_add"), use_container_width=True, key="acc_add"):
            item = {
                "platform": platform, 
                "username": username, 
                "group": group, 
                "tags": [t.strip() for t in tags.split(",") if t.strip()], 
                "refresh_minutes": int(refresh), 
                "updated_at": datetime.now().isoformat()
            }
            found = False
            for i, a in enumerate(db["accounts"]):
                if a["platform"] == platform and a["username"] == username:
                    # Preserve existing session file if not updating it
                    if "session_file" in a:
                        item["session_file"] = a["session_file"]
                    db["accounts"][i] = item
                    found = True
                    break
            if not found:
                db["accounts"].append(item)
            
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            log_admin_op("accounts_upsert", {"platform": platform, "username": username})
            st.success(tr("acc_save_success"))
            st.rerun()

    with tabs[1]:
        st.info("支持批量上传 Session 文件。如果是 .session 文件，将自动识别为 Telegram 账号；其他文件需手动指定平台。")
        
        imp_platform = st.selectbox("默认平台 (若无法自动识别)", ["Telegram", "WhatsApp", "WeChat", "Twitter"], key="imp_platform")
        imp_group = st.text_input("默认分组", value="Imported", key="imp_group")
        imp_tags = st.text_input("默认标签", value="batch_import", key="imp_tags")
        
        uploaded_files = st.file_uploader("选择文件 (支持多选)", accept_multiple_files=True, key="acc_uploader")
        
        if uploaded_files and st.button("开始导入", type="primary", use_container_width=True):
            count = 0
            for up_file in uploaded_files:
                fname = up_file.name
                # Determine platform and username
                f_platform = imp_platform
                f_username = os.path.splitext(fname)[0]
                
                if fname.endswith(".session"):
                    f_platform = "Telegram"
                elif fname.endswith(".json"):
                     # Try to read platform from json? For now use default or filename hint
                     pass
                
                # Save file
                safe_fname = f"{f_platform}_{f_username}_{fname}" # Avoid collision
                # But typically for telethon session, filename matters if we use it directly. 
                # Let's keep original filename if possible, but store in a safe way.
                # Ideally: data/tenants/{tid}/sessions/{filename}
                # If collision, overwrite? Yes for update.
                save_path = os.path.join(sessions_dir, fname)
                with open(save_path, "wb") as f:
                    f.write(up_file.getbuffer())
                
                # 尝试识别真实用户名 (Telegram)
                if f_platform == "Telegram" and fname.endswith(".session"):
                    api_id = os.getenv("TELEGRAM_API_ID")
                    api_hash = os.getenv("TELEGRAM_API_HASH")
                    if api_id and api_hash:
                        with st.spinner(f"正在连接 Telegram 识别账号信息 ({fname})..."):
                            try:
                                # 临时运行 loop 获取信息
                                real_user = asyncio.run(get_session_user(save_path, api_id, api_hash))
                                if real_user:
                                    f_username = real_user
                                    st.toast(f"✅ 成功识别: {f_username}")
                                else:
                                    st.warning(f"无法识别账号信息，使用文件名作为用户名: {f_username}")
                            except Exception as e:
                                print(f"Session识别错误: {e}")

                # Update DB
                item = {
                    "platform": f_platform,
                    "username": f_username,
                    "group": imp_group,
                    "tags": [t.strip() for t in imp_tags.split(",") if t.strip()],
                    "refresh_minutes": 60,
                    "updated_at": datetime.now().isoformat(),
                    "session_file": fname, # Store relative filename in sessions dir
                    "status": "unused",    # Default status for new import
                    "note": "等待首次验证"  # Default note
                }
                
                # Upsert
                found = False
                for i, a in enumerate(db["accounts"]):
                    if a["platform"] == f_platform and a["username"] == f_username:
                        db["accounts"][i] = item
                        found = True
                        break
                if not found:
                    db["accounts"].append(item)
                count += 1
            
            # Save DB
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            
            log_admin_op("accounts_import", {"count": count, "tenant": tenant})
            st.success(f"成功导入 {count} 个账号！")
            st.rerun()

    with tabs[2]:
        st.markdown(tr("acc_list_title"))
        
        # 准备数据，为每行生成唯一 ID
        disp_accounts = []
        for idx, item in enumerate(db["accounts"]):
            new_item = item.copy()
            # 内部记录索引，用于后续操作
            new_item["Idx"] = idx  # Rename from _index to Idx to avoid reserved column name error
            
            if "updated_at" in new_item:
                new_item["updated_at"] = format_time(new_item["updated_at"])
            
            # Session Status & Account Status
            status_val = "⚠️ 未配置"
            
            # 优先使用数据库存储的 status
            db_status = new_item.get("status", "")
            db_note = new_item.get("note", "")
            
            # 显示映射
            status_map = {
                "unused": "🆕 未使用",
                "active": "✅ 正常",
                "error": "❌ 异常"
            }
            
            # 如果数据库已有明确状态，优先显示
            if db_status in status_map:
                status_val = status_map[db_status]
            else:
                # 兼容旧数据逻辑
                if "session_file" in new_item and new_item["session_file"]:
                    s_path = os.path.join(sessions_dir, new_item["session_file"])
                    if os.path.exists(s_path):
                        sz = os.path.getsize(s_path)
                        if sz > 0:
                            new_item["Session"] = f"✅ ({int(sz/1024)}KB)"
                            status_val = "🆕 未使用" # 有文件但无状态记录，默认为未使用
                        else:
                            new_item["Session"] = "❌ (Empty)"
                            status_val = "❌ 空文件"
                    else:
                        new_item["Session"] = "❌ (Missing)"
                        status_val = "❌ 文件丢失"
                else:
                    new_item["Session"] = "-"
                    status_val = "⚠️ 无Session"
            
            new_item["Status"] = status_val
            new_item["Note"] = db_note
            
            if not new_item.get("username"):
                new_item["username"] = "(未命名)" 
            
            disp_accounts.append(new_item)
        
        if disp_accounts:
            # 转换为 DataFrame
            df = pd.DataFrame(disp_accounts)
            
            # 配置列显示，隐藏 Idx
            column_config = {
                "Idx": None, # Hide Idx column
                "platform": "平台",
                "username": "用户名",
                "group": "分组",
                "tags": "标签",
                "refresh_minutes": "刷新间隔(分)",
                "updated_at": "更新时间",
                "session_file": "Session文件",
                "Session": "Session状态",
                "Status": "账号状态",
                "Note": "备注"
            }
            
            # 使用 data_editor 增加勾选框
            # 增加一个 'selected' 列用于勾选
            df.insert(0, "Select", False)
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "选择",
                        help="勾选以进行批量操作",
                        default=False,
                    ),
                    **column_config
                },
                disabled=["platform", "username", "group", "tags", "refresh_minutes", "updated_at", "session_file", "Session", "Status", "Note"],
                hide_index=True,
                use_container_width=True,
                key="acc_list_editor"
            )
            
            # 获取被选中的行
            selected_rows = edited_df[edited_df["Select"] == True]
            
            if not selected_rows.empty:
                st.markdown("### 批量操作")
                c1, c2, c3 = st.columns([1, 1, 4])
                
                with c1:
                    if st.button("🔍 验证有效性", type="secondary", key="acc_batch_verify"):
                        # 获取索引
                        indices_to_verify = sorted(selected_rows["Idx"].tolist())
                        
                        api_id = os.getenv("TELEGRAM_API_ID")
                        api_hash = os.getenv("TELEGRAM_API_HASH")
                        
                        if not api_id or not api_hash:
                            st.error("请先在 .env 中配置 TELEGRAM_API_ID 和 TELEGRAM_API_HASH")
                        else:
                            current_accounts = db["accounts"]
                            updated_count = 0
                            
                            progress_bar = st.progress(0)
                            
                            for i, idx in enumerate(indices_to_verify):
                                if 0 <= idx < len(current_accounts):
                                    acc = current_accounts[idx]
                                    platform = acc.get("platform")
                                    
                                    if platform == "Telegram" and acc.get("session_file"):
                                        s_path = os.path.join(sessions_dir, acc["session_file"])
                                        if os.path.exists(s_path):
                                            try:
                                                # 尝试连接验证
                                                real_user = asyncio.run(get_session_user(s_path, api_id, api_hash))
                                                if real_user:
                                                    acc["status"] = "active"
                                                    acc["note"] = f"Verified at {datetime.now().strftime('%H:%M')}"
                                                    # 更新用户名（如果之前是未命名或旧名）
                                                    acc["username"] = real_user
                                                else:
                                                    acc["status"] = "error"
                                                    acc["note"] = "验证失败: 无法获取用户信息 (Auth Key可能失效)"
                                            except Exception as e:
                                                acc["status"] = "error"
                                                acc["note"] = f"验证异常: {str(e)}"
                                        else:
                                            acc["status"] = "error"
                                            acc["note"] = "文件不存在"
                                    else:
                                        acc["note"] = "不支持自动验证的平台"
                                        
                                    acc["updated_at"] = datetime.now().isoformat()
                                    updated_count += 1
                                
                                progress_bar.progress((i + 1) / len(indices_to_verify))
                                
                            # 保存
                            db["accounts"] = current_accounts
                            with open(db_path, "w", encoding="utf-8") as f:
                                json.dump(db, f, ensure_ascii=False, indent=2)
                                
                            st.success(f"已完成 {updated_count} 个账号的验证！")
                            st.rerun()

                with c2:
                    if st.button("🗑️ 批量删除", type="primary", key="acc_batch_del"):
                        # 获取要删除的索引 (降序排列，防止删除导致索引错位)
                        indices_to_delete = sorted(selected_rows["Idx"].tolist(), reverse=True)
                        
                        deleted_count = 0
                        current_accounts = db["accounts"]
                        
                        for idx in indices_to_delete:
                            if 0 <= idx < len(current_accounts):
                                acc = current_accounts[idx]
                                # 删除关联的 Session 文件
                                if "session_file" in acc:
                                    s_path = os.path.join(sessions_dir, acc["session_file"])
                                    if os.path.exists(s_path):
                                        try:
                                            os.remove(s_path)
                                        except:
                                            pass
                                
                                # 从列表中移除
                                del current_accounts[idx]
                                deleted_count += 1
                                
                        # 保存更新
                        db["accounts"] = current_accounts
                        with open(db_path, "w", encoding="utf-8") as f:
                            json.dump(db, f, ensure_ascii=False, indent=2)
                            
                        log_admin_op("accounts_batch_delete", {"count": deleted_count})
                        st.success(f"成功删除 {deleted_count} 个账号！")
                        st.rerun()
            
        else:
            st.info("暂无账号")

def render_orchestrator_panel():
    st.header(f"🧩 {tr('orch_header')}")
    _render_scope_hint("当前租户全平台生效")
    tenant_id = st.session_state.get("tenant", "default")
    tab_labels = [tr("orch_tab_stage"), tr("orch_tab_persona"), tr("orch_tab_binding"), "模拟决策", "批量评估", "风格守卫", "健康检查"]
    tabs = st.tabs(tab_labels)

    def _is_stage_name_ok(name):
        return name in ["S0","S1","S2","S3","S4","S5"]
    def _json_or_error(label, text):
        try:
            if not text.strip():
                st.error(f"{label}: 空内容")
                return None
            obj = json.loads(text)
            if not isinstance(obj, dict):
                st.error(f"{label}: 需为对象JSON")
                return None
            return obj
        except Exception as e:
            st.error(f"{label}: JSON解析失败 - {e}")
            return None
    def _validate_binding(obj):
        ok = True
        routes = obj.get("routes") or []
        for i, r in enumerate(routes, 1):
            stg = r.get("stage") or "*"
            per = r.get("persona") or "*"
            if stg != "*" and not _is_stage_name_ok(stg):
                st.error(f"绑定规则#{i}: Stage 非法")
                ok = False
            temp = float(r.get("temperature", 0.7))
            if temp < 0.0 or temp > 1.0:
                st.error(f"绑定规则#{i}: temperature 超出范围 [0,1]")
                ok = False
            imin = r.get("intent_min")
            imax = r.get("intent_max")
            if imin is not None and (float(imin) < 0.0 or float(imin) > 1.0):
                st.error(f"绑定规则#{i}: intent_min 超出范围 [0,1]")
                ok = False
            if imax is not None and (float(imax) < 0.0 or float(imax) > 1.0):
                st.error(f"绑定规则#{i}: intent_max 超出范围 [0,1]")
                ok = False
            rmax = r.get("risk_max")
            if rmax is not None and str(rmax).lower() not in ["low","medium","high","unknown"]:
                st.error(f"绑定规则#{i}: risk_max 取值非法")
                ok = False
            mlen = r.get("min_msg_len")
            if mlen is not None and int(mlen) < 0:
                st.error(f"绑定规则#{i}: min_msg_len 需≥0")
                ok = False
        d = obj.get("default") or {}
        t2 = float(d.get("temperature", 0.7))
        if t2 < 0.0 or t2 > 1.0:
            st.error("默认绑定: temperature 超出范围 [0,1]")
            ok = False
        return ok

    with tabs[0]:
        st.subheader("流程阶段配置")
        name = st.selectbox("选择或创建阶段", ["S0","S1","S2","S3","S4","S5"], key="orch_stage_name_sel")
        version = st.text_input("版本号", value="v1", key="orch_stage_ver")
        existing = db.get_script_profile_by_name(tenant_id, "stage", name, version)
        init_json = existing.get("content") or "{}"
        adv_mode = st.toggle("高级模式（JSON）", value=False, key="orch_stage_adv")
        def _stage_cache_path(tenant_id, name, version):
            base_dir = os.path.join(os.path.dirname(__file__), "data", "cache")
            os.makedirs(base_dir, exist_ok=True)
            fname = f"stage_struct_{tenant_id}_{name}_{version}.json"
            return os.path.join(base_dir, fname)
        def _load_stage_cache(tenant_id, name, version):
            p = _stage_cache_path(tenant_id, name, version)
            try:
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
            except:
                return None
            return None
        def _save_stage_cache(tenant_id, name, version, struct):
            p = _stage_cache_path(tenant_id, name, version)
            try:
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(struct, f, ensure_ascii=False, indent=2)
            except:
                pass
        def _clear_stage_cache(tenant_id, name, version):
            p = _stage_cache_path(tenant_id, name, version)
            try:
                if os.path.exists(p):
                    os.remove(p)
            except:
                pass
        if st.session_state.get("stage_struct_loaded_for") != (tenant_id, name, version):
            cached = _load_stage_cache(tenant_id, name, version)
            if cached and isinstance(cached, dict):
                st.session_state["stage_struct"] = cached
            else:
                try:
                    obj_init = json.loads(init_json)
                    st.session_state["stage_struct"] = {"nodes": obj_init.get("nodes") or [{"id":"start","type":"start","label":"开始"},{"id":"end","type":"end","label":"结束"}], "transitions": obj_init.get("transitions") or []}
                except:
                    st.session_state["stage_struct"] = {"nodes":[{"id":"start","type":"start","label":"开始"},{"id":"end","type":"end","label":"结束"}],"transitions":[]}
            st.session_state["stage_struct_loaded_for"] = (tenant_id, name, version)
        def _json_to_struct(obj):
            nodes = obj.get("nodes") or []
            trans = obj.get("transitions") or []
            if not isinstance(nodes, list): nodes = []
            if not isinstance(trans, list): trans = []
            return {"nodes": nodes, "transitions": trans}
        def _struct_to_json(struct):
            return {"nodes": struct.get("nodes") or [], "transitions": struct.get("transitions") or []}
        def _validate_stage_struct(struct):
            nodes = struct.get("nodes") or []
            trans = struct.get("transitions") or []
            ids = {n.get("id") for n in nodes if n.get("id")}
            start_nodes = [n for n in nodes if n.get("type") == "start"]
            end_nodes = [n for n in nodes if n.get("type") == "end"]
            if len(start_nodes) != 1:
                st.error("必须且仅有一个开始节点")
                return False
            if len(end_nodes) < 1:
                st.error("至少需要一个结束节点")
                return False
            for i, t in enumerate(trans, 1):
                if t.get("from") not in ids or t.get("to") not in ids:
                    st.error(f"跳转#{i}: 引用未知节点")
                    return False
            reach = set()
            start_id = start_nodes[0].get("id")
            stack = [start_id]
            graph = {}
            for t in trans:
                graph.setdefault(t.get("from"), []).append(t.get("to"))
            while stack:
                cur = stack.pop()
                if cur in reach: continue
                reach.add(cur)
                for nxt in graph.get(cur, []):
                    if nxt not in reach:
                        stack.append(nxt)
            unreachable = [n.get("id") for n in nodes if n.get("id") not in reach]
            if unreachable:
                st.warning(f"不可达节点: {', '.join(unreachable)}")
            return True
        if adv_mode:
            content = st.text_area("Stage JSON", value=init_json, height=180, key="orch_stage_json")
            if st.button("从 JSON 载入结构", use_container_width=True, key="orch_stage_load_json"):
                obj = _json_or_error("Stage", content or "{}")
                if obj is not None:
                    st.session_state["stage_struct"] = _json_to_struct(obj)
                    _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                    st.success("已载入 JSON 到结构化编辑器")
            if st.button("保存 JSON 版本", use_container_width=True, key="orch_stage_save_json"):
                obj = _json_or_error("Stage", content or "{}")
                if obj is not None:
                    db.upsert_script_profile(tenant_id, "stage", name, version or "v1", content or "{}", True)
                    log_admin_op("orch_stage_save", {"tenant": tenant_id, "name": name, "version": version or "v1"})
                    _clear_stage_cache(tenant_id, name, version)
                    st.success("已保存")
            up = st.file_uploader("导入 JSON", type=["json"], key="stage_import")
            if up:
                try:
                    data = json.loads(up.getvalue().decode("utf-8"))
                    st.session_state["stage_struct"] = _json_to_struct(data)
                    _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                    st.success("导入成功")
                except Exception as e:
                    st.error(f"导入失败: {e}")
            export_data = init_json
            st.download_button("导出当前版本", data=export_data, file_name=f"{name}-{version}.json", mime="application/json", use_container_width=True)
        else:
            struct = st.session_state["stage_struct"]
            cols = st.columns(2)
            with cols[0]:
                st.markdown("节点列表")
                st.table(struct.get("nodes") or [])
                nid = st.text_input("节点ID", key="stage_nid")
                ntype = st.selectbox("类型", ["normal","start","end"], key="stage_ntype")
                nlabel = st.text_input("显示名称", key="stage_nlabel")
                if st.button("添加/更新节点", use_container_width=True, key="btn_add_node"):
                    nodes = [n for n in struct["nodes"] if n.get("id") != nid]
                    nodes.append({"id": nid, "type": ntype, "label": nlabel})
                    st.session_state["stage_struct"]["nodes"] = nodes
                    _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                    st.success("节点已更新")
                del_id = st.text_input("删除节点ID", key="stage_del_id")
                force_del = st.toggle("强制删除", value=False, key="stage_force_del")
                if st.button("删除节点", use_container_width=True, key="btn_del_node"):
                    nodes = [n for n in struct.get("nodes", []) if n.get("id") != del_id]
                    trans = [t for t in struct.get("transitions", []) if t.get("from") != del_id and t.get("to") != del_id]
                    st.session_state["stage_struct"]["nodes"] = nodes
                    st.session_state["stage_struct"]["transitions"] = trans
                    _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                    st.success("节点已删除")
                fix_illegal = st.toggle("修复非法类型为 normal", value=False, key="stage_fix_illegal")
                if st.button("执行类型修复", use_container_width=True, key="btn_fix_types"):
                    allowed = {"normal","start","end"}
                    nodes = []
                    for n in struct.get("nodes", []):
                        t = n.get("type")
                        if t not in allowed:
                            n["type"] = "normal"
                        nodes.append(n)
                    st.session_state["stage_struct"]["nodes"] = nodes
                    _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                    st.success("类型修复完成")
            with cols[1]:
                st.markdown("跳转规则")
                st.table(struct.get("transitions") or [])
                tf = st.text_input("来源节点", key="stage_t_from")
                tt = st.text_input("目标节点", key="stage_t_to")
                cond = st.text_input("条件表达式", key="stage_t_cond")
                if st.button("添加跳转", use_container_width=True, key="btn_add_trans"):
                    trans = struct.get("transitions") or []
                    trans.append({"from": tf, "to": tt, "condition": cond})
                    st.session_state["stage_struct"]["transitions"] = trans
                    _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                    st.success("跳转已添加")
                dtf = st.text_input("删除跳转来源", key="stage_dt_from")
                dtt = st.text_input("删除跳转目标", key="stage_dt_to")
                if st.button("删除跳转", use_container_width=True, key="btn_del_trans"):
                    trans = [t for t in struct.get("transitions", []) if not (t.get("from") == dtf and t.get("to") == dtt)]
                    st.session_state["stage_struct"]["transitions"] = trans
                    _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                    st.success("跳转已删除")
                connect_unreachable = st.toggle("连接不可达节点到 end", value=False, key="stage_connect_unreach")
                if st.button("执行连接修复", use_container_width=True, key="btn_fix_unreach"):
                    nodes = struct.get("nodes") or []
                    trans = struct.get("transitions") or []
                    ids = {n.get("id") for n in nodes if n.get("id")}
                    start_nodes = [n for n in nodes if n.get("type") == "start"]
                    end_nodes = [n for n in nodes if n.get("type") == "end"]
                    if start_nodes and end_nodes:
                        start_id = start_nodes[0].get("id")
                        end_id = end_nodes[0].get("id")
                        reach = set()
                        stack = [start_id]
                        graph = {}
                        for t in trans:
                            graph.setdefault(t.get("from"), []).append(t.get("to"))
                        while stack:
                            cur = stack.pop()
                            if cur in reach: continue
                            reach.add(cur)
                            for nxt in graph.get(cur, []):
                                if nxt not in reach:
                                    stack.append(nxt)
                        for nid in ids:
                            if nid not in reach and nid != end_id:
                                trans.append({"from": nid, "to": end_id, "condition": ""})
                        st.session_state["stage_struct"]["transitions"] = trans
                        _save_stage_cache(tenant_id, name, version, st.session_state["stage_struct"])
                        st.success("不可达节点已连接到 end")
            ok = _validate_stage_struct(st.session_state["stage_struct"])
            if ok and st.button("保存为新版本", use_container_width=True, key="btn_save_struct"):
                obj = _struct_to_json(st.session_state["stage_struct"])
                db.upsert_script_profile(tenant_id, "stage", name, version or "v1", json.dumps(obj, ensure_ascii=False), True)
                log_admin_op("orch_stage_save", {"tenant": tenant_id, "name": name, "version": version or "v1"})
                _clear_stage_cache(tenant_id, name, version)
                st.success("已保存")
            st.divider()
            st.markdown("历史版本")
            versions = [p for p in db.get_script_profiles(tenant_id, "stage") if p.get("name") == name]
            disp = [{"version": p.get("version"), "created_at": p.get("created_at")} for p in versions]
            if disp:
                st.table(disp)
            if st.button("从草稿恢复", use_container_width=True, key="btn_restore_draft"):
                cached = _load_stage_cache(tenant_id, name, version)
                if cached:
                    st.session_state["stage_struct"] = cached
                    st.success("草稿已恢复")
                else:
                    st.info("无可用草稿")
        st.divider()
        st.info("配置向导：需包含开始与结束节点；跳转条件填写为布尔表达式或关键字匹配表达，保存前会自动检测错误并提示")
    with tabs[1]:
        st.subheader("Persona 表达风格配置")
        presets = [
            {"name":"calm_professional","params":{"tone":"calm","speed":"medium","empathy":"medium","humor":False,"directness":"moderate"}},
            {"name":"friendly_helpful","params":{"tone":"friendly","speed":"medium","empathy":"high","humor":True,"directness":"low"}},
            {"name":"firm_efficiency","params":{"tone":"formal","speed":"fast","empathy":"low","humor":False,"directness":"high"}}
        ]
        preset_names = [p["name"] for p in presets]
        sel_preset = st.selectbox("选择预设模板", preset_names, key="persona_preset")
        name = st.text_input("Persona 名称", value=sel_preset, key="orch_persona_name")
        version = st.text_input("版本号", value="v1", key="orch_persona_ver")
        base = next((p for p in presets if p["name"] == sel_preset), presets[0])
        params = base["params"].copy()
        tone = st.selectbox("语调", ["calm","friendly","formal","enthusiastic"], index=["calm","friendly","formal","enthusiastic"].index(params["tone"]), key="persona_tone")
        speed = st.selectbox("语速", ["slow","medium","fast"], index=["slow","medium","fast"].index(params["speed"]), key="persona_speed")
        empathy = st.selectbox("情感倾向", ["low","medium","high"], index=["low","medium","high"].index(params["empathy"]), key="persona_empathy")
        humor = st.toggle("幽默", value=bool(params["humor"]), key="persona_humor")
        directness = st.selectbox("直接程度", ["low","moderate","high"], index=["low","moderate","high"].index(params["directness"]), key="persona_direct")
        adv_mode_p = st.toggle("高级模式（JSON）", value=False, key="persona_adv")
        def _build_preview(tone, speed, empathy, humor, directness):
            sample = "这是一个预览示例回复。"
            if tone == "friendly": sample = "嗨～很高兴帮你，这个问题我来处理！"
            elif tone == "formal": sample = "您好，您的问题已收到，我将为您详细说明。"
            elif tone == "enthusiastic": sample = "太棒了！这个需求我们可以快速搞定！"
            else: sample = "好的，我来协助你，先确认一下关键信息。"
            if speed == "slow": sample += " 我会一步步说明，确保清晰。"
            elif speed == "fast": sample += " 我将直接给出结论与下一步。"
            if empathy == "high": sample += " 我理解你的担忧，我们会一同解决。"
            if humor: sample += " 顺便说一句，今天状态不错呢。"
            if directness == "high": sample += " 结论明确，请按此方案执行。"
            return sample
        if adv_mode_p:
            init = {"name": name, "version": version, "params": {"tone": tone, "speed": speed, "empathy": empathy, "humor": humor, "directness": directness}}
            content = st.text_area("Persona JSON", value=json.dumps(init, ensure_ascii=False, indent=2), height=180, key="persona_json")
            if st.button("保存 JSON 版本", use_container_width=True, key="persona_save_json"):
                obj = _json_or_error("Persona", content or "{}")
                if obj is not None:
                    db.upsert_script_profile(tenant_id, "persona", name, version or "v1", content or "{}", True)
                    log_admin_op("orch_persona_save", {"tenant": tenant_id, "name": name, "version": version or "v1"})
                    st.success("已保存")
            up = st.file_uploader("导入 Persona JSON", type=["json"], key="persona_import")
            if up:
                try:
                    data = json.loads(up.getvalue().decode("utf-8"))
                    p = data.get("params") or {}
                    st.session_state["persona_tone"] = p.get("tone","calm")
                    st.session_state["persona_speed"] = p.get("speed","medium")
                    st.session_state["persona_empathy"] = p.get("empathy","medium")
                    st.session_state["persona_humor"] = bool(p.get("humor", False))
                    st.session_state["persona_direct"] = p.get("directness","moderate")
                    st.success("导入成功")
                except Exception as e:
                    st.error(f"导入失败: {e}")
        else:
            preview = _build_preview(tone, speed, empathy, humor, directness)
            st.markdown("实时预览")
            st.info(preview)
            if st.button("保存为新版本", use_container_width=True, key="persona_save_struct"):
                payload = {"name": name, "version": version, "params": {"tone": tone, "speed": speed, "empathy": empathy, "humor": humor, "directness": directness}}
                db.upsert_script_profile(tenant_id, "persona", name, version or "v1", json.dumps(payload, ensure_ascii=False), True)
                log_admin_op("orch_persona_save", {"tenant": tenant_id, "name": name, "version": version or "v1"})
                st.success("已保存")
            st.divider()
            st.markdown("历史版本")
            versions = [p for p in db.get_script_profiles(tenant_id, "persona") if p.get("name") == name]
            disp = [{"version": p.get("version"), "created_at": p.get("created_at")} for p in versions]
            if disp:
                st.table(disp)
    with tabs[2]:
        st.subheader("🔗 绑定关系 (Binding)")
        st.caption("定义不同 Stage/Persona/Intent 条件下使用的具体 AI 模型与参数。")
        
        # Helper: Show available models
        with st.expander("📚 查看可用模型列表 (Reference)", expanded=False):
            try:
                base = _ensure_data_dirs()
                p_path = os.path.join(base, "tenants", tenant_id, "ai_providers.json")
                if os.path.exists(p_path):
                    with open(p_path, "r", encoding="utf-8") as f:
                        p_cfg = json.load(f)
                    st.markdown("**可用的 'model' 标识符:**")
                    for p in p_cfg.get("providers", []):
                        pid = f"{p['provider']}:{p['model']}" if p.get('model') else p['provider']
                        remark = f" ({p['remark']})" if p.get('remark') else ""
                        st.code(f"{pid}", language="text")
                        st.caption(f"👆 {p.get('model')}{remark} - {p['provider']}")
                else:
                    st.warning("尚未配置模型，请前往 AGNT AI 配置中心")
            except Exception:
                pass

        existing = db.get_script_profile_by_name(tenant_id, "binding", "binding_default", "v1")
        init = existing.get("content") or "{}"
        content = st.text_area(tr("orch_binding_content"), value=init, height=300, key="orch_binding_content", help="JSON 格式。在 'model' 字段中使用上方列表中的标识符。")
        
        if st.button(tr("orch_btn_save_binding"), use_container_width=True, key="orch_binding_save"):
            obj = _json_or_error("Binding", content or "{}")
            if obj is not None and _validate_binding(obj):
                db.upsert_script_profile(tenant_id, "binding", "binding_default", "v1", content or "{}", True)
                log_admin_op("orch_binding_save", {"tenant": tenant_id})
                st.success(tr("orch_save_success"))

    with tabs[3]:
        st.subheader("模拟决策")
        # Allow params from query params if "Replay" was triggered
        qp = st.query_params
        def_stage = qp.get("replay_stage", "S0")
        if def_stage not in ["S0","S1","S2","S3","S4","S5"]: def_stage = "S0"
        
        sim_stage = st.selectbox("Stage", ["S0","S1","S2","S3","S4","S5"], index=["S0","S1","S2","S3","S4","S5"].index(def_stage), key="sim_stage")
        sim_persona = st.text_input("Persona", value=qp.get("replay_persona", "calm_professional"), key="sim_persona")
        sim_intent = st.slider("intent_score", 0.0, 1.0, float(qp.get("replay_intent", 0.5)), 0.01, key="sim_intent")
        sim_risk = st.selectbox("risk_level", ["low","medium","high","unknown"], index=["low","medium","high","unknown"].index(qp.get("replay_risk", "low")), key="sim_risk")
        sim_msg = st.text_input("消息文本", value=qp.get("replay_msg", "hello"), key="sim_msg")
        
        if st.button("执行模拟", use_container_width=True, key="sim_run"):
            from stage_agent_runtime import StageAgentRuntime
            stager = StageAgentRuntime(tenant_id)
            state = {"current_stage": sim_stage, "persona_id": sim_persona, "intent_score": float(sim_intent), "risk_level": sim_risk}
            ctx = {"kb_hits": 0, "msg_len": len(sim_msg), "intent_score": float(sim_intent), "risk_level": sim_risk}
            res = stager.resolve_binding(state, ctx)
            st.json(res)
            r = res.get("matched_rule")
            if r:
                st.success(f"命中规则: score={r.get('_final_score')}")
            else:
                st.info("未命中，使用默认")

    with tabs[4]:
        # Batch Eval (existing)
        st.subheader("批量评估")
        st.caption("输入 JSON List 测试用例，批量验证路由策略。")
        default_cases = [
            {"stage": "S1", "persona": "calm_professional", "msg": "hi", "intent": 0.2, "risk": "low"},
            {"stage": "S3", "persona": "sales_closer", "msg": "how much?", "intent": 0.9, "risk": "low"},
            {"stage": "S1", "persona": "*", "msg": "angry!!", "intent": 0.5, "risk": "high"}
        ]
        cases_json = st.text_area("测试用例集 (JSON List)", value=json.dumps(default_cases, indent=2), height=200, key="batch_cases")
        
        if st.button("开始批量评估", key="batch_run"):
            try:
                cases = json.loads(cases_json)
                if not isinstance(cases, list):
                    st.error("测试用例必须是列表格式")
                else:
                    from stage_agent_runtime import StageAgentRuntime
                    runtime = StageAgentRuntime(tenant_id)
                    results = []
                    progress_bar = st.progress(0)
                    for i, case in enumerate(cases):
                        state = {
                            "current_stage": case.get("stage", "S0"),
                            "persona_id": case.get("persona", "default"),
                            "intent_score": case.get("intent", 0.0),
                            "risk_level": case.get("risk", "unknown")
                        }
                        ctx = {
                            "kb_hits": case.get("kb_hits", 0),
                            "msg_len": len(case.get("msg", "")),
                            "intent_score": case.get("intent", 0.0),
                            "risk_level": case.get("risk", "unknown")
                        }
                        res = runtime.resolve_binding(state, ctx)
                        rule = res.get("matched_rule", {})
                        results.append({
                            "Case": f"#{i+1}",
                            "Stage": state["current_stage"],
                            "Persona": state["persona_id"],
                            "Risk": state["risk_level"],
                            "Intent": state["intent_score"],
                            "Model": res.get("model"),
                            "Temp": res.get("temperature"),
                            "Score": rule.get("_final_score", 0),
                            "RuleWeight": rule.get("weight", "default")
                        })
                        progress_bar.progress((i + 1) / len(cases))
                    st.dataframe(results)
                    import pandas as pd
                    df = pd.DataFrame(results)
                    st.markdown("### 统计报告")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**模型分布**")
                        st.write(df["Model"].value_counts())
                    with c2:
                        st.markdown("**规则权重分布**")
                        st.write(df["RuleWeight"].value_counts())
            except json.JSONDecodeError:
                st.error("JSON 格式错误")
            except Exception as e:
                st.error(f"评估出错: {e}")

    with tabs[5]:
        st.subheader("🛡️ 风格守卫 (Regex Guard)")
        st.caption("基于正则表达式的后处理规则，用于拦截或修正“机器人味”过重的回复。")
        st.info("💡 提示：如需更高级的语义审核（如色情、暴力检测），请前往 'AGNT AI 配置中心' 开启 LLM 审计功能。")
        
        sg_prof = db.get_script_profile_by_name(tenant_id, "style_guard", "style_default", "v1")
        sg_content = sg_prof.get("content") or json.dumps({
            "identity_patterns": [
                r"(?i)作为\s*AI[，,。]*",
                r"(?i)作为\s*一个\s*AI[，,。]*",
                r"(?i)我是\s*AI[，,。]*"
            ],
            "max_questions": 1
        }, indent=2, ensure_ascii=False)
        
        new_sg = st.text_area("Style Guard JSON", value=sg_content, height=300, key="sg_editor")
        if st.button("保存 Style Guard 配置"):
            try:
                parsed = json.loads(new_sg)
                if not isinstance(parsed, dict):
                    st.error("配置必须是 JSON 对象")
                else:
                    db.upsert_script_profile(tenant_id, "style_guard", "style_default", "v1", new_sg)
                    st.success("Style Guard 配置已保存")
                    log_admin_op("update_style_guard", {"tenant": tenant_id})
            except json.JSONDecodeError as e:
                st.error(f"JSON 格式错误: {e}")

    with tabs[6]:
        st.subheader("🏥 系统配置健康检查")
        if st.button("开始检查", key="health_check_btn"):
            issues = []
            
            # 1. 检查 AI Models Config
            base = _ensure_data_dirs()
            p_path = os.path.join(base, "tenants", tenant_id, "ai_providers.json")
            has_models = False
            if os.path.exists(p_path):
                try:
                    with open(p_path, "r", encoding="utf-8") as f:
                        p_cfg = json.load(f)
                        if p_cfg.get("providers"):
                            has_models = True
                except: pass
            
            if not has_models:
                issues.append("❌ 未配置任何 AI 模型 (请前往 AGNT AI 配置中心 -> 模型注册表)")
            
            # 2. 检查 Telegram Config & Pipeline
            tg_conf_path = os.path.join(base, "tenants", tenant_id, "platforms", "telegram", "config.txt")
            if not os.path.exists(tg_conf_path):
                issues.append(f"⚠️ 缺少 Telegram 配置文件")
            else:
                try:
                    with open(tg_conf_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "CONV_ORCHESTRATION=on" not in content:
                            issues.append("⚠️ 编排模式 (Supervisor) 未开启")
                except:
                    pass
            
            # 3. 检查 Stage 配置
            stages = db.get_script_profiles(tenant_id, "stage")
            if not stages:
                issues.append("❌ 未定义任何 Stage (Stage Script)")
            else:
                stage_names = [s['name'] for s in stages]
                if "S0" not in stage_names:
                    issues.append("⚠️ 建议定义初始阶段 S0")
            
            # 4. 检查 Persona
            personas = db.get_script_profiles(tenant_id, "persona")
            if not personas:
                issues.append("❌ 未定义任何 Persona")
            
            # 5. 检查 Binding
            binding = db.get_script_profile_by_name(tenant_id, "binding", "binding_default", "v1")
            if not binding:
                issues.append("⚠️ 未定义路由绑定策略 (Binding)，将使用默认逻辑")
            
            if not issues:
                st.success("✅ 系统配置健康！")
            else:
                for issue in issues:
                    if "❌" in issue:
                        st.error(issue)
                    else:
                        st.warning(issue)

def render_supervisor_panel():
    st.header(f"🛰️ {tr('sup_header')}")
    _render_scope_hint("当前租户全平台生效（只读/回放）")
    tenant_id = st.session_state.get("tenant", "default")
    
    tab1, tab2 = st.tabs(["会话管理", "决策回放"])
    
    with tab1:
        st.subheader(tr("sup_list_title"))
        
        # Manual Load / Refresh
        col_ctrl1, col_ctrl2 = st.columns([1, 3])
        with col_ctrl1:
            if st.button("🔄 刷新会话列表", key="sup_refresh_btn", use_container_width=True):
                st.session_state.sup_refresh_trigger = datetime.now().timestamp()
                st.rerun()
        
        # Load data (with spinner and error handling)
        try:
            with st.spinner("正在加载会话数据..."):
                sessions = db.list_conversation_states(tenant_id, limit=50)
        except Exception as e:
            st.error(f"加载会话失败: {e}")
            sessions = []

        disp = []
        for s in sessions:
            r = s.copy()
            r["updated_at"] = format_time(r.get("updated_at"))
            disp.append(r)
        if disp:
            st.dataframe(disp)
        else:
            st.info("暂无会话数据或加载为空")

        choices = [f"{s.get('platform')}:{s.get('user_id')}" for s in sessions]
        sel = st.selectbox(tr("sup_select_user"), choices or ["-"], key="sup_sel")
        
        # Add Delete Context Button
        if st.button("🗑️ 删除 AI 上下文记忆", key="sup_btn_del_ctx", help="删除选中用户的对话记忆，重置为初始状态"):
            if sel and sel != "-":
                try:
                    if ":" in sel:
                        platform_x, user_id_x = sel.split(":", 1)
                        db.delete_conversation_state(tenant_id, platform_x, user_id_x)
                        st.success(f"✅ 已删除 {sel} 的上下文记忆")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 删除失败: {e}")
            else:
                st.warning("⚠️ 请先选择一个会话")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            stage = st.selectbox(tr("sup_force_stage"), ["S0","S1","S2","S3","S4","S5"], key="sup_stage")
        with c2:
            persona = st.text_input(tr("sup_force_persona"), value="calm_professional", key="sup_persona")
        with c3:
            handoff = st.checkbox(tr("sup_handoff"), value=False, key="sup_handoff")
            
        if st.button(tr("sup_btn_apply"), use_container_width=True, key="sup_apply"):
            try:
                if ":" in sel:
                    platform, user_id = sel.split(":", 1)
                    cur = db.get_conversation_state(tenant_id, platform, user_id)
                    cur["current_stage"] = stage
                    cur["persona_id"] = persona
                    cur["handoff_required"] = bool(handoff)
                    db.upsert_conversation_state(tenant_id, platform, user_id, cur)
                    st.success(tr("sup_apply_success"))
                    st.rerun()
            except Exception as e:
                st.error(str(e))
                
    with tab2:
        st.subheader(tr("sup_route_title"))
        routes = db.get_routing_decisions(tenant_id, limit=50)
        
        # Display as a table with expandable details
        if not routes:
            st.info("暂无路由记录")
        else:
            for i, r in enumerate(routes):
                dec = r.get("decision") or {}
                ctx = dec.get("context") or {}
                matched = dec.get("matched_rule") or {}
                
                # Summary line
                ts = format_time(r.get("created_at"))
                user = r.get("user_id")
                model = dec.get("model")
                score = matched.get("_final_score", 0)
                
                with st.expander(f"{ts} | User: {user} | Model: {model} (Score: {score})"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**输入上下文**")
                        st.json(ctx)
                    with c2:
                        st.markdown("**决策结果**")
                        st.json(matched)
                    
                    # Replay Button
                    # Link to Orchestrator Simulation Tab with params
                    # Since we can't easily jump tabs with params in Streamlit without hack,
                    # we will show a button that says "Load into Simulation" and sets query params
                    if st.button("🔁 加载到模拟器", key=f"replay_{i}"):
                        st.query_params["replay_stage"] = ctx.get("current_stage", "S0")
                        st.query_params["replay_persona"] = ctx.get("persona_id", "default")
                        st.query_params["replay_intent"] = str(ctx.get("intent_score", 0.5))
                        st.query_params["replay_risk"] = ctx.get("risk_level", "low")
                        st.query_params["replay_msg"] = ctx.get("user_msg", "")
                        st.success("参数已加载！请切换到【编排面板 -> 模拟决策】查看。")

def render_ai_config_panel():
    st.header("🧠 AGNT AI配置中心")
    _render_scope_hint("当前租户全平台生效")
    base = _ensure_data_dirs()
    tenant = st.session_state.get("tenant", "default")
    tdir = os.path.join(base, "tenants", tenant)
    os.makedirs(tdir, exist_ok=True)
    cfg_path = os.path.join(tdir, "ai_providers.json")
    
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        else:
            cfg = {"providers": []}
    except Exception:
        cfg = {"providers": []}
        
    tab1, tab2 = st.tabs(["🤖 模型注册表 (Model Registry)", "⛓️ 会话智能体配置 (Session Agent Pipeline)"])

    # --- Tab 1: Model Registry ---
    with tab1:
        st.caption(tr("acc_tenant").format(tenant))
        st.markdown(tr("ai_subtitle"))
        col1, col2, col3 = st.columns(3)
        with col1:
            provider = st.selectbox(tr("ai_provider"), ["DeepSeek", "OpenAI", "AzureOpenAI", "LocalAI", "Google", "Anthropic"], key="ai_provider")
            base_url = st.text_input(tr("ai_base_url"), key="ai_base_url")
        with col2:
            model = st.text_input(tr("ai_model"), key="ai_model")
            weight = st.slider(tr("ai_weight"), 0, 100, 50, key="ai_weight")
        with col3:
            api_key = st.text_input(tr("ai_api_key"), type="password", key="ai_api_key")
            timeout = st.number_input(tr("ai_timeout"), min_value=1, max_value=60, value=30, step=1, key="ai_timeout")
        
        remark = st.text_input("备注 (Remark)", placeholder="例如：用于逻辑分析的主模型", key="ai_remark")

        if st.button(tr("common_save"), use_container_width=True, key="ai_save_cfg"):
            item = {
                "provider": provider, 
                "base_url": base_url, 
                "model": model, 
                "weight": int(weight), 
                "timeout": int(timeout), 
                "remark": remark,
                "updated_at": datetime.now().isoformat()
            }
            # Add API Key only if provided (don't overwrite with empty if editing?) 
            # Actually current logic doesn't store API Key in list display, but saves to file.
            # We should probably save it. The original code didn't load it back into the UI for security.
            # But here we are writing the whole item.
            # Wait, original code: item = {...}, then cfg["providers"][i] = item.
            # This implies if I don't provide API key, it might be lost if I overwrite?
            # Original code: log_admin_op(..., "api_key": api_key).
            # The original code DOES NOT save API key to `ai_providers.json`?
            # Wait, line 4448 says "API Key 不保存在列表中；仅用于运行时加载".
            # If it's not saved in JSON, where is it saved?
            # "仅用于运行时加载, 请考虑环境变量". This implies the JSON is just for metadata?
            # BUT `handlers.py` needs the API key to run!
            # If the user enters an API Key here, it MUST be saved somewhere.
            # Let's check the original code again.
            # Original code: `json.dump(cfg, ...)`
            # The item dictionary created DOES NOT include api_key initially?
            # line 4425: `item = {"provider": provider...}` NO api_key.
            # So the original code was BROKEN or intended for env var usage only?
            # The user wants "Configure corresponding AI model".
            # I MUST save the API Key for this to work dynamically.
            if api_key:
                item["api_key"] = api_key
            
            found = False
            for i, p in enumerate(cfg["providers"]):
                if p["provider"] == provider and p.get("model") == model:
                    # Preserve existing key if not provided
                    if "api_key" not in item and "api_key" in p:
                        item["api_key"] = p["api_key"]
                    cfg["providers"][i] = item
                    found = True
                    break
            if not found:
                cfg["providers"].append(item)
                
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            log_admin_op("ai_provider_upsert", {"provider": provider, "model": model})
            st.success(tr("common_success"))
            st.rerun()
            
        st.divider()
        st.markdown("已配置列表")
        disp_providers = []
        for item in cfg["providers"]:
            new_item = item.copy()
            if "updated_at" in new_item:
                new_item["updated_at"] = format_time(new_item["updated_at"])
            # Mask API Key for display
            if "api_key" in new_item:
                new_item["api_key"] = "******"
            disp_providers.append(new_item)
        st.table(disp_providers)

    # --- Tab 2: Session Agent Pipeline ---
    with tab2:
        st.markdown("### ⛓️ AI 会话链路配置")
        st.caption("在此配置会话过程中各环节使用的 AI 模型。如果某个环节选择不使用，系统将尝试绕过该环节。")
        
        # Load Telegram Config (as the main config source for now)
        tg_conf_path = os.path.join(tdir, "platforms", "telegram", "config.txt")
        current_conf = {}
        if os.path.exists(tg_conf_path):
            with open(tg_conf_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        current_conf[k.strip()] = v.strip()
        
        # Prepare Model Options
        # Logic: If tenant != default, we do NOT show "System Default".
        # We want to force new tenants to configure their own models.
        model_opts = []
        
        # Check if we should allow System Default
        # For now, only 'default' tenant or SuperAdmin might see it?
        # But user requirement is: "Normal new user... should input LLM first".
        # So for non-default tenants, we remove "System Default".
        
        if tenant == "default":
             model_opts.append(("default", "系统默认 (System Default)"))
        else:
             # Add a placeholder if empty, but it won't be selectable for execution
             model_opts.append(("", "请选择... (Please Select)"))
        
        for p in cfg["providers"]:
            pid = f"{p['provider']}:{p['model']}" if p.get('model') else p['provider']
            # Format: ModelName (Remark) - Provider
            # Example: gpt-4o (测试用) - OpenAI
            pname = p.get('model') or "Unknown Model"
            if p.get('remark'):
                pname += f" ({p['remark']})"
            else:
                pname += " (无备注)"
            pname += f" - {p['provider']}"
            
            model_opts.append((pid, pname))
        
        # If no models configured for this tenant, show info instead of warning
        if len(model_opts) == 1 and model_opts[0][0] == "":
             st.info("💡 提示：当前暂无可用的 AI 模型。请先切换到 '🤖 模型注册表' 标签页添加模型，然后在此处进行选择。")
        
        # Helper to get index
        def _get_idx(val):
            # If val is 'default' but we removed it (because tenant!=default), index will be 0 (Please Select)
            for i, (k, _) in enumerate(model_opts):
                if k == val: return i
            return 0

        # 1. Supervisor
        st.markdown("#### 1. 🧠 场控 (Supervisor)")
        c1, c2 = st.columns([1, 3])
        with c1:
            # Reusing CONV_ORCHESTRATION as the master switch for Supervisor logic
            sup_enabled = st.toggle("启用场控", value=(current_conf.get("CONV_ORCHESTRATION", "off").lower() == "on"), key="pipe_sup_en")
        with c2:
            sup_model = st.selectbox("选择模型", model_opts, index=_get_idx(current_conf.get("MODEL_SUPERVISOR")), format_func=lambda x: x[1], key="pipe_sup_model", disabled=not sup_enabled)

        # 2. Worker (Stage Agent)
        st.markdown("#### 2. 🎭 执行者 (Worker / Stage Agent)")
        c1, c2 = st.columns([1, 3])
        with c1:
            st.info("执行者是核心生成模块，受场控调度。")
        with c2:
            worker_model = st.selectbox("选择模型", model_opts, index=_get_idx(current_conf.get("MODEL_WORKER")), format_func=lambda x: x[1], key="pipe_worker_model")

        # 3. Audit Primary
        st.markdown("#### 3. 🛡️ 初审 (Audit Primary)")
        c1, c2 = st.columns([1, 3])
        with c1:
            audit_p_enabled = st.toggle("启用初审", value=(current_conf.get("AUDIT_ENABLED", "on").lower() == "on"), key="pipe_audit_p_en")
        with c2:
            audit_p_model = st.selectbox("选择模型", model_opts, index=_get_idx(current_conf.get("MODEL_AUDIT_PRIMARY")), format_func=lambda x: x[1], key="pipe_audit_p_model", disabled=not audit_p_enabled)

        # 4. Audit Secondary
        st.markdown("#### 4. ⚖️ 复审 (Audit Secondary)")
        c1, c2 = st.columns([1, 3])
        with c1:
            audit_s_enabled = st.toggle("启用复审 (双重审计)", value=(current_conf.get("ENABLE_AUDIT_SECONDARY", "off").lower() == "on"), key="pipe_audit_s_en")
        with c2:
            audit_s_model = st.selectbox("选择模型", model_opts, index=_get_idx(current_conf.get("MODEL_AUDIT_SECONDARY")), format_func=lambda x: x[1], key="pipe_audit_s_model", disabled=not audit_s_enabled)

        if st.button("💾 保存链路配置", type="primary", key="pipe_save"):
            # Validation: Ensure models are selected if enabled
            if sup_enabled and not sup_model:
                 st.error("❌ 启用场控必须选择有效的模型")
                 st.stop()
            if not worker_model:
                 st.error("❌ 执行者必须选择有效的模型")
                 st.stop()
            if audit_p_enabled and not audit_p_model:
                 st.error("❌ 启用初审必须选择有效的模型")
                 st.stop()
            if audit_s_enabled and not audit_s_model:
                 st.error("❌ 启用复审必须选择有效的模型")
                 st.stop()

            # Update config dict
            current_conf["CONV_ORCHESTRATION"] = "on" if sup_enabled else "off"
            current_conf["MODEL_SUPERVISOR"] = sup_model[0]
            current_conf["MODEL_WORKER"] = worker_model[0]
            
            current_conf["AUDIT_ENABLED"] = "on" if audit_p_enabled else "off"
            current_conf["MODEL_AUDIT_PRIMARY"] = audit_p_model[0]
            
            current_conf["ENABLE_AUDIT_SECONDARY"] = "on" if audit_s_enabled else "off"
            current_conf["MODEL_AUDIT_SECONDARY"] = audit_s_model[0]
            
            # Write back
            try:
                os.makedirs(os.path.dirname(tg_conf_path), exist_ok=True)
                with open(tg_conf_path, "w", encoding="utf-8") as f:
                    for k, v in current_conf.items():
                        f.write(f"{k}={v}\n")
                st.success("配置已保存！")
                log_admin_op("pipeline_config_update", current_conf)
            except Exception as e:
                st.error(f"保存失败: {e}")

def _list_ai_bind_options(tenant: str):
    base = _ensure_data_dirs()
    tdir = os.path.join(base, "tenants", tenant)
    os.makedirs(tdir, exist_ok=True)
    cfg_path = os.path.join(tdir, "ai_providers.json")
    providers = []
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            providers = cfg.get("providers") or []
    except Exception:
        providers = []
    options = [("all", "全部/不绑定")]
    for p in providers:
        provider = (p.get("provider") or "").strip()
        model = (p.get("model") or "").strip()
        if not provider and not model:
            continue
        ai_id = f"{provider}:{model}" if model else provider
        label = f"{provider} / {model}" if model else provider
        options.append((ai_id, label))
    return options

def render_ai_learning_panel():
    st.header("🧪 AI学习中心")
    _render_scope_hint("当前租户全平台生效")
    tenant_id = st.session_state.get("tenant", "default")
    counts = db.get_learning_counts(tenant_id)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("总记录", counts.get("total", 0))
    with c2:
        st.metric("可学习", counts.get("learnable", 0))
    with c3:
        st.metric("垃圾/过滤", counts.get("junk", 0))

    tab_browse, tab_export = st.tabs(["📄 数据浏览与清洗", "📦 导出学习集"])

    ai_opts = _list_ai_bind_options(tenant_id)
    ai_opt_map = {k: v for k, v in ai_opts}

    with tab_browse:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            platform = st.selectbox("平台", ["all", "telegram", "whatsapp"], index=1, key="learn_f_platform")
        with f2:
            direction = st.selectbox("方向", ["all", "outbound", "inbound"], index=0, key="learn_f_direction")
        with f3:
            learnable = st.selectbox("可学习", ["all", "1", "0"], index=0, key="learn_f_learnable")
        with f4:
            junk = st.selectbox("垃圾", ["all", "1", "0"], index=0, key="learn_f_junk")

        g1, g2, g3 = st.columns(3)
        with g1:
            bind_ai = st.selectbox("绑定AI", [k for k, _ in ai_opts], format_func=lambda x: ai_opt_map.get(x, x), key="learn_f_ai")
        with g2:
            keyword = st.text_input("关键词", value="", key="learn_f_kw")
        with g3:
            limit = st.number_input("每页数量", min_value=50, max_value=500, value=200, step=50, key="learn_f_limit")

        is_learnable = None
        if learnable in ("0", "1"):
            is_learnable = int(learnable)
        is_junk = None
        if junk in ("0", "1"):
            is_junk = int(junk)

        rows = db.list_message_events(
            tenant_id=tenant_id,
            platform=platform,
            direction=direction,
            is_learnable=is_learnable,
            is_junk=is_junk,
            learning_ai_id=bind_ai,
            keyword=keyword.strip() or None,
            limit=int(limit),
            offset=0,
        )

        if not rows:
            st.info("暂无数据")
        else:
            import pandas as pd
            view = []
            for r in rows:
                view.append({
                    "select": False,
                    "id": r.get("id"),
                    "platform": r.get("platform"),
                    "direction": r.get("direction"),
                    "status": r.get("status"),
                    "is_junk": int(r.get("is_junk") or 0),
                    "is_learnable": int(r.get("is_learnable") or 0),
                    "learning_ai_id": r.get("learning_ai_id") or "",
                    "learning_tags": r.get("learning_tags") or "",
                    "timestamp": format_time(r.get("timestamp")),
                    "user_content": (r.get("user_content") or "")[:500],
                    "bot_response": (r.get("bot_response") or "")[:500],
                })
            df = pd.DataFrame(view)
            edited = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "select": st.column_config.CheckboxColumn("选择"),
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "platform": st.column_config.TextColumn("平台", disabled=True),
                    "direction": st.column_config.TextColumn("方向", disabled=True),
                    "status": st.column_config.TextColumn("状态", disabled=True),
                    "timestamp": st.column_config.TextColumn("时间", disabled=True),
                    "user_content": st.column_config.TextColumn("用户内容", width="large", disabled=True),
                    "bot_response": st.column_config.TextColumn("机器人回复", width="large", disabled=True),
                },
                key="learn_editor",
            )
            selected_ids = [int(x) for x in edited.loc[edited["select"] == True, "id"].tolist()]

            st.divider()
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                mark_learnable = st.selectbox("设置可学习", ["不修改", "标记为可学习", "标记为不可学习"], index=0, key="learn_act_learnable")
            with a2:
                mark_junk = st.selectbox("设置垃圾", ["不修改", "标记为垃圾", "标记为非垃圾"], index=0, key="learn_act_junk")
            with a3:
                bind_ai_act = st.selectbox("绑定到AI", [k for k, _ in ai_opts], format_func=lambda x: ai_opt_map.get(x, x), key="learn_act_ai")
            with a4:
                tags = st.text_input("标签(逗号分隔)", value="", key="learn_act_tags")

            apply_btn = st.button("✅ 应用到已选择记录", width="stretch", key="learn_apply")
            if apply_btn:
                if not selected_ids:
                    st.warning("请先勾选要操作的记录")
                else:
                    is_learnable_act = None
                    if mark_learnable == "标记为可学习":
                        is_learnable_act = 1
                    elif mark_learnable == "标记为不可学习":
                        is_learnable_act = 0
                    is_junk_act = None
                    if mark_junk == "标记为垃圾":
                        is_junk_act = 1
                    elif mark_junk == "标记为非垃圾":
                        is_junk_act = 0
                    ai_val = None
                    if bind_ai_act != "all":
                        ai_val = bind_ai_act
                    updated = db.update_message_learning_flags(
                        ids=selected_ids,
                        is_junk=is_junk_act,
                        is_learnable=is_learnable_act,
                        learning_ai_id=ai_val,
                        learning_tags=tags.strip() if tags.strip() else None,
                    )
                    log_admin_op("learning_batch_update", {"count": len(selected_ids)})
                    st.success(f"✅ 已提交更新 ({len(selected_ids)} 条)")
                    st.rerun()

            st.divider()
            d1, d2 = st.columns([1, 3])
            with d1:
                confirm_del = st.checkbox("确认删除", value=False, key="learn_confirm_del")
            with d2:
                if st.button("🗑️ 删除已选择记录", width="stretch", disabled=not confirm_del, key="learn_delete"):
                    if not selected_ids:
                        st.warning("请先勾选要删除的记录")
                    else:
                        db.delete_message_events(selected_ids)
                        log_admin_op("learning_batch_delete", {"count": len(selected_ids)})
                        st.success(f"✅ 已删除 ({len(selected_ids)} 条)")
                        st.rerun()

    with tab_export:
        st.subheader("导出可学习集")
        ex1, ex2, ex3 = st.columns(3)
        with ex1:
            ex_platform = st.selectbox("平台", ["all", "telegram", "whatsapp"], index=0, key="learn_ex_platform")
        with ex2:
            ex_ai = st.selectbox("绑定AI", [k for k, _ in ai_opts], format_func=lambda x: ai_opt_map.get(x, x), key="learn_ex_ai")
        with ex3:
            ex_limit = st.number_input("导出数量上限", min_value=10, max_value=5000, value=500, step=50, key="learn_ex_limit")

        if st.button("📦 导出 JSONL", width="stretch", key="learn_export_btn"):
            rows = db.list_message_events(
                tenant_id=tenant_id,
                platform=ex_platform,
                is_learnable=1,
                is_junk=0,
                learning_ai_id=ex_ai,
                limit=int(ex_limit),
                offset=0,
            )
            export_items = []
            for r in rows:
                u = (r.get("user_content") or "").strip()
                a = (r.get("bot_response") or "").strip()
                if not u or not a:
                    continue
                export_items.append({"input": u, "output": a, "meta": {"id": r.get("id"), "platform": r.get("platform"), "ai": r.get("learning_ai_id") or ""}})
            base = _ensure_data_dirs()
            out_dir = os.path.join(base, "tenants", tenant_id, "learning_exports")
            os.makedirs(out_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_path = os.path.join(out_dir, f"learnset-{ts}.jsonl")
            with open(out_path, "w", encoding="utf-8") as f:
                for item in export_items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            log_admin_op("learning_export", {"count": len(export_items), "path": out_path})
            st.success(f"✅ 已导出 {len(export_items)} 条：{out_path}")

def render_skills_panel():
    st.header("🧩 技能中心")
    _render_scope_hint("当前租户全平台生效（可按 AI 业务线绑定）")
    tenant_id = st.session_state.get("tenant", "default")
    ai_opts = _list_ai_bind_options(tenant_id)
    ai_opt_map = {k: v for k, v in ai_opts}

    tab_list, tab_edit = st.tabs(["📋 技能列表", "➕ 新增/编辑"])

    with tab_list:
        skills = db.list_skills(tenant_id)
        if not skills:
            st.info("暂无技能配置")
        else:
            import pandas as pd
            rows = []
            for s in skills:
                rows.append({
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "enabled": bool(s.get("enabled")),
                    "bound_ai_id": s.get("bound_ai_id") or "",
                    "updated_at": format_time(s.get("updated_at")),
                    "description": s.get("description") or "",
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            sel = st.selectbox("选择技能ID", ["-"] + [r["id"] for r in rows], key="skill_sel_id")
            c1, c2 = st.columns([1, 3])
            with c1:
                confirm_del = st.checkbox("确认删除", value=False, key="skill_confirm_del")
            with c2:
                if st.button("🗑️ 删除技能", use_container_width=True, disabled=(not confirm_del or sel == "-"), key="skill_del_btn"):
                    db.delete_skill(tenant_id, sel)
                    log_admin_op("skill_delete", {"skill_id": sel})
                    st.success("✅ 已删除")
                    st.rerun()

    with tab_edit:
        skills = db.list_skills(tenant_id)
        by_id = {s.get("id"): s for s in skills}
        edit_id = st.selectbox("编辑已有技能(可选)", ["-"] + list(by_id.keys()), key="skill_edit_id")
        cur = by_id.get(edit_id, {}) if edit_id != "-" else {}
        name = st.text_input("技能名称", value=cur.get("name") or "", key="skill_name")
        desc = st.text_area("技能说明", value=cur.get("description") or "", height=80, key="skill_desc")
        is_new = (edit_id == "-")
        default_enabled = False if is_new else bool(cur.get("enabled", False))
        enabled = st.checkbox("启用", value=default_enabled, key="skill_enabled")
        bound_ai = st.selectbox("绑定到AI业务线", [k for k, _ in ai_opts], index=0, format_func=lambda x: ai_opt_map.get(x, x), key="skill_ai_bind")

        cfg = cur.get("config") or {}
        skill_type = st.selectbox("技能类型", ["prompt", "rule"], index=0 if cfg.get("type") != "rule" else 1, key="skill_type")
        apply_mode = st.selectbox("适用回复路径", ["kb_only", "script_only", "both"], index=2 if cfg.get("apply_mode") == "both" else (1 if cfg.get("apply_mode") == "script_only" else 0), key="skill_apply_mode")
        prompt_tpl = st.text_area("Prompt模板/规则说明", value=cfg.get("template") or "", height=180, key="skill_tpl")

        if st.button("💾 保存技能", use_container_width=True, key="skill_save_btn"):
            payload = {
                "id": cur.get("id") if edit_id != "-" else None,
                "name": name.strip(),
                "description": desc.strip(),
                "enabled": bool(enabled),
                "bound_ai_id": "" if bound_ai == "all" else bound_ai,
                "config": {
                    "type": skill_type,
                    "apply_mode": apply_mode,
                    "template": prompt_tpl,
                },
            }
            sid = db.upsert_skill(tenant_id, payload)
            log_admin_op("skill_upsert", {"skill_id": sid})
            st.success("✅ 已保存")
            st.rerun()

def render_api_gateway_panel():
    st.header(f"🛣️ {tr('api_header')}")
    _render_scope_hint("当前租户全平台生效")
    base = _ensure_data_dirs()
    tenant = st.session_state.get("tenant", "default")
    tdir = os.path.join(base, "tenants", tenant)
    os.makedirs(tdir, exist_ok=True)
    gw_path = os.path.join(tdir, "api_gateway.json")
    try:
        if os.path.exists(gw_path):
            with open(gw_path, "r", encoding="utf-8") as f:
                gw = json.load(f)
        else:
            gw = {"routes": []}
    except Exception:
        gw = {"routes": []}
    st.caption(f"当前租户: {tenant}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        route = st.text_input(tr('api_route_path'), key="gw_route")
    with col2:
        method = st.selectbox(tr('api_route_method'), ["GET","POST","PUT","DELETE"], key="gw_method")
    with col3:
        auth = st.selectbox(tr('api_route_auth'), ["None","Token","HMAC"], key="gw_auth")
    with col4:
        rate = st.number_input(tr('api_route_rate'), min_value=0, max_value=10000, value=60, step=10, key="gw_rate")
    if st.button(tr('api_btn_add'), width="stretch", key="gw_add"):
        item = {"route": route, "method": method, "auth": auth, "rate_limit": int(rate), "updated_at": datetime.now().isoformat()}
        found = False
        for i, r in enumerate(gw["routes"]):
            if r["route"] == route and r["method"] == method:
                gw["routes"][i] = item
                found = True
                break
        if not found:
            gw["routes"].append(item)
        with open(gw_path, "w", encoding="utf-8") as f:
            json.dump(gw, f, ensure_ascii=False, indent=2)
        log_admin_op("api_route_upsert", {"route": route, "method": method})
        st.success(tr('api_save_success'))
        st.rerun()
    st.divider()
    st.markdown(tr('api_list_header'))
    disp_routes = []
    for item in gw["routes"]:
        new_item = item.copy()
        if "updated_at" in new_item:
            new_item["updated_at"] = format_time(new_item["updated_at"])
        disp_routes.append(new_item)
    st.table(disp_routes)

def _vault_paths(tenant):
    base = _ensure_data_dirs()
    tdir = os.path.join(base, "tenants", tenant)
    os.makedirs(tdir, exist_ok=True)
    return {
        "key": os.path.join(tdir, "vault.key"),
        "secrets": os.path.join(tdir, "secrets.json"),
        # 租户隔离的环境变量文件
        "env": os.path.join(tdir, ".env"),
        # 租户隔离的 Session 文件
        "user_session": os.path.join(tdir, "sessions", "userbot_session.session"),
        "admin_session": os.path.join(tdir, "sessions", "admin_session.session"),
    }

def render_sys_config_panel():
    st.header(f"🧩 {tr('sys_header')}")
    _render_scope_hint("全平台生效")
    tenant = st.session_state.get("tenant", "default")
    paths = _vault_paths(tenant)
    key_bytes = _ensure_vault_key(paths["key"])
    
    # Ensure sessions dir exists
    os.makedirs(os.path.dirname(paths["user_session"]), exist_ok=True)
    
    colA, colB = st.columns(2)
    with colA:
        st.subheader(tr('sys_env_header'))
        env_exists = os.path.exists(paths["env"])
        st.metric(tr('sys_status'), tr('sys_status_gen') if env_exists else tr('sys_status_not_gen'))
        st.caption(tr('sys_file_path').format(paths['env']))
        
        # Load existing if available (for UX, masked)
        # Note: In a real secure env, we might not want to pre-fill unless explicitly requested
        
        api_id = st.text_input("TELEGRAM_API_ID", placeholder="不展示明文", key="env_api_id")
        api_hash = st.text_input("TELEGRAM_API_HASH", placeholder="不展示明文", type="password", key="env_api_hash")
        ai_key = st.text_input("AI_API_KEY", placeholder="不展示明文", type="password", key="env_ai_key")
        base_url = st.text_input("AI_BASE_URL", value="https://api.55.ai/v1", key="env_ai_base")
        model = st.text_input("AI_MODEL_NAME", value="deepseek-v3.1", key="env_ai_model")
        
        if st.button(tr('sys_btn_gen_env'), use_container_width=True, key="btn_gen_env"):
            try:
                # Backup old env if exists
                if os.path.exists(paths["env"]):
                    backup_dir = os.path.join(os.path.dirname(paths["env"]), "backups")
                    os.makedirs(backup_dir, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                    shutil.copy2(paths["env"], os.path.join(backup_dir, f".env.{ts}.bak"))
                
                content = [
                    f"TELEGRAM_API_ID={api_id}",
                    f"TELEGRAM_API_HASH={api_hash}",
                    f"AI_API_KEY={ai_key}",
                    f"AI_BASE_URL={base_url}",
                    f"AI_MODEL_NAME={model}",
                ]
                with open(paths["env"], "w", encoding="utf-8") as f:
                    f.write("\n".join(content) + "\n")
                
                # Encrypt secrets
                secrets_path = paths["secrets"]
                data = {}
                if os.path.exists(secrets_path):
                    with open(secrets_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                data.update({
                    "TELEGRAM_API_ID": _encrypt(api_id, key_bytes),
                    "TELEGRAM_API_HASH": _encrypt(api_hash, key_bytes),
                    "AI_API_KEY": _encrypt(ai_key, key_bytes)
                })
                with open(secrets_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                log_admin_op("env_generate", {"tenant": tenant})
                st.success(tr('sys_success_env'))
            except Exception as e:
                st.error(f"生成失败: {e}")
                
    with colB:
        st.subheader(tr('sys_session_header'))
        user_exists = os.path.exists(paths["user_session"])
        admin_exists = os.path.exists(paths["admin_session"])
        st.metric("userbot_session", tr('sys_status_gen') if user_exists else tr('sys_status_not_gen'))
        st.metric("admin_session", tr('sys_status_gen') if admin_exists else tr('sys_status_not_gen'))
        if st.button(tr('sys_btn_init_session'), use_container_width=True, key="btn_init_sessions"):
            try:
                if not user_exists:
                    open(paths["user_session"], "wb").close()
                if not admin_exists:
                    shutil.copy2(paths["user_session"], paths["admin_session"])
                log_admin_op("session_init", {"tenant": tenant})
                st.success(tr('sys_success_session'))
                st.rerun()
            except Exception as e:
                st.error(f"初始化失败: {e}")
    st.divider()
    st.subheader("敏感信息加密与查看")
    st.caption("默认显示为掩码；查看需二次验证并记录审计日志")
    secrets_path = paths["secrets"]
    secrets = {}
    try:
        if os.path.exists(secrets_path):
            with open(secrets_path, "r", encoding="utf-8") as f:
                secrets = json.load(f)
    except Exception:
        secrets = {}
    masked = {k: ("*****" if v else "") for k, v in secrets.items()}
    st.table([{"键": k, "值": masked[k]} for k in masked])
    code_state_key = "view_code"
    if code_state_key not in st.session_state:
        st.session_state[code_state_key] = None
    colv1, colv2 = st.columns(2)
    with colv1:
        if st.button("生成二次验证码", key="btn_gen_code"):
            import secrets
            st.session_state[code_state_key] = str(secrets.randbelow(900000) + 100000)
            st.info("已生成，请输入验证码进行查看")
    with colv2:
        input_code = st.text_input("输入验证码以查看", key="input_view_code")
        if st.button("查看明文", key="btn_view_plain"):
            if input_code and input_code == st.session_state.get(code_state_key):
                try:
                    plain = {k: _decrypt(v, key_bytes) for k, v in secrets.items() if v}
                    log_admin_op("secret_view", {"tenant": tenant})
                    st.success("✅ 验证通过（当前会话有效）")
                    st.json(plain)
                except Exception as e:
                    st.error(f"解密失败: {e}")
            else:
                st.error("验证码不正确")
    with st.expander("系统升级与数据保留", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            from_ver = st.text_input("当前版本", value="v_current", key="upgrade_from")
        with c2:
            to_ver = st.text_input("目标版本", value="v_target", key="upgrade_to")
        c3, c4, c5 = st.columns(3)
        with c3:
            if st.button("预升级检查", key="btn_precheck"):
                try:
                    db_path = db.db_path
                    abs_db = os.path.join(BASE_DIR, db_path) if not os.path.isabs(db_path) else db_path
                    ok_db = os.path.exists(abs_db)
                    size = os.path.getsize(abs_db) if ok_db else 0
                    backups_dir = os.path.join(BASE_DIR, "data", "backups")
                    try:
                        os.makedirs(backups_dir, exist_ok=True)
                        test_file = os.path.join(backups_dir, ".perm.test")
                        open(test_file, "w").close()
                        os.remove(test_file)
                        perm_ok = True
                    except Exception:
                        perm_ok = False
                    st.metric("数据库存在", "是" if ok_db else "否")
                    st.metric("数据库大小字节", f"{size}")
                    st.metric("备份目录写入权限", "可写" if perm_ok else "不可写")
                    st.success("检查完成")
                except Exception as e:
                    st.error(f"检查失败: {e}")
        with c4:
            if st.button("数据备份", key="btn_backup"):
                try:
                    backup_path = db.backup_all()
                    st.session_state["last_backup"] = backup_path
                    st.success(f"已备份: {backup_path}")
                except Exception as e:
                    st.error(f"备份失败: {e}")
        with c5:
            if st.button("执行升级", key="btn_upgrade"):
                log_id = None
                try:
                    backup_path = st.session_state.get("last_backup", "")
                    log_id = db.start_upgrade_log(from_ver, to_ver, backup_path, {"precheck": "done"})
                    db._migrate_tables()
                    db.finish_upgrade_log(log_id, "success", {"message": "migrated"})
                    st.success("升级完成")
                except Exception as e:
                    if log_id:
                        db.finish_upgrade_log(log_id, "failed", {"error": str(e)})
                    st.error(f"升级失败: {e}")
        st.divider()
        backups_dir = os.path.join(BASE_DIR, "data", "backups")
        backups = []
        try:
            if os.path.isdir(backups_dir):
                backups = [os.path.join(backups_dir, d) for d in os.listdir(backups_dir)]
                backups = sorted([p for p in backups if os.path.isdir(p)], reverse=True)
        except Exception:
            backups = []
        selected_backup = st.selectbox("选择备份用于回滚", backups, format_func=lambda p: os.path.basename(p) if p else "", index=0 if backups else 0)
        if st.button("回滚恢复", key="btn_rollback"):
            try:
                if selected_backup:
                    db.restore_backup(selected_backup)
                    st.success("已从备份恢复")
                else:
                    st.warning("无可用备份")
            except Exception as e:
                st.error(f"回滚失败: {e}")
        st.divider()
        try:
            logs = db.list_upgrade_logs(50)
            if logs:
                st.table([{
                    "ID": r.get("id"),
                    "From": r.get("version_from"),
                    "To": r.get("version_to"),
                    "状态": r.get("status"),
                    "备份": r.get("backup_path"),
                    "开始": r.get("started_at"),
                    "结束": r.get("finished_at"),
                } for r in logs])
            else:
                st.info("暂无升级日志")
        except Exception as e:
            st.error(f"日志读取失败: {e}")

    with st.expander("权限清理与重置", expanded=False):
        can_run = (st.session_state.get("user_role") == "SuperAdmin")
        st.caption("操作将删除数据库中所有非superAdmin角色记录")
        code_key = "perm_cleanup_code"
        if code_key not in st.session_state:
            import secrets as _secrets
            st.session_state[code_key] = str(_secrets.randbelow(900000) + 100000)
        st.info(f"确认码: {st.session_state[code_key]}")
        input_code = st.text_input("输入确认码以继续", key="input_perm_cleanup")
        if st.button("执行清理", disabled=not can_run):
            if input_code == st.session_state.get(code_key):
                try:
                    affected = db.cleanup_non_superadmin_roles()
                    log_admin_op("perm_cleanup_roles", {"affected": affected})
                    st.success(f"已清理 {affected} 条记录")
                except Exception as e:
                    st.error(f"清理失败: {e}")
            else:
                st.error("验证码不正确")
def render_business_panel():
    st.header(f"📊 {tr('bus_header')}")
    _render_scope_hint("全平台生效")
    tenant = st.session_state.get("tenant", "default")
    bc = BusinessCore(tenant)
    try:
        import pandas as pd  # 可选依赖
    except Exception:
        pd = None
    
    tab1, tab2, tab3 = st.tabs([tr("bus_tab_dashboard"), tr("bus_tab_sub"), tr("bus_tab_brand")])
    
    with tab1:
        st.subheader(tr("bus_metrics_core"))
        stats = bc.get_dashboard_data()
        
        # Real Metrics
        c1, c2, c3, c4 = st.columns(4)
        
        # 1. Active Users (7 days)
        active_users = stats.get("active_users", 0)
        c1.metric(tr("bus_active_users"), f"{active_users}", help="近7日活跃用户数")
        
        # 2. Total Tokens
        total_tokens = stats.get("total_tokens", 0)
        c2.metric(tr("bus_total_tokens"), f"{total_tokens:,}")
        
        # 3. Total Cost
        total_cost = stats.get("total_cost", 0.0)
        c3.metric(tr("bus_total_cost"), f"${total_cost:,.4f}")
        
        # 4. Revenue (Mock)
        c4.metric(tr("bus_revenue"), "$12,450", "+22%")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader(tr("bus_trend"))
            # Real Message Trend Data
            msg_trend = stats.get("daily_messages", {})
            if msg_trend:
                if pd:
                    df_trend = pd.DataFrame(list(msg_trend.items()), columns=['Date', 'Messages'])
                    df_trend.set_index('Date', inplace=True)
                    st.line_chart(df_trend)
                else:
                    st.table([{"Date": d, "Messages": v} for d, v in msg_trend.items()])
            else:
                st.info("暂无趋势数据")

        with col_chart2:
            st.subheader(tr("bus_cost_breakdown"))
            cost_by_stage = stats.get("cost_by_stage", {})
            if cost_by_stage:
                if pd:
                    df_cost = pd.DataFrame(list(cost_by_stage.items()), columns=['Stage', 'Cost'])
                    df_cost.set_index('Stage', inplace=True)
                    st.bar_chart(df_cost)
                else:
                    st.table([{"Stage": s, "Cost": c} for s, c in cost_by_stage.items()])
            else:
                st.info("暂无成本分布数据")
        
        st.subheader(tr("bus_funnel"))
        funnel = stats.get("conversion_funnel", {})
        if pd:
            f_data = pd.DataFrame.from_dict(funnel, orient='index', columns=['Count'])
            st.bar_chart(f_data)
        else:
            st.table([{"Step": k, "Count": v} for k, v in funnel.items()])

    with tab2:
        st.subheader(tr("bus_sub_plan"))
        config = bc.get_subscription_info()
        current_plan = config.get("plan", "free")
        
        st.info(f"{tr('bus_current_plan')}: {current_plan.upper()} | {tr('bus_expiry')}: {config.get('subscription_end', '-')}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"### {tr('bus_plan_free_title')}")
            st.markdown(tr("bus_plan_free_feat1"))
            st.markdown(tr("bus_plan_free_feat2"))
            if st.button(tr("bus_plan_free_btn"), key="plan_free", disabled=(current_plan=="free")):
                if bc.upgrade_plan("free"): st.rerun()
        with c2:
            st.markdown(f"### {tr('bus_plan_pro_title')}")
            st.markdown(tr("bus_plan_pro_feat1"))
            st.markdown(tr("bus_plan_pro_feat2"))
            st.markdown(tr("bus_plan_pro_feat3"))
            if st.button(tr("bus_plan_pro_btn"), key="plan_pro", disabled=(current_plan=="pro")):
                if bc.upgrade_plan("pro"): st.rerun()
        with c3:
            st.markdown(f"### {tr('bus_plan_ent_title')}")
            st.markdown(tr("bus_plan_ent_feat1"))
            st.markdown(tr("bus_plan_ent_feat2"))
            st.markdown(tr("bus_plan_ent_feat3"))
            if st.button(tr("bus_plan_ent_btn"), key="plan_ent", disabled=(current_plan=="enterprise")):
                if bc.upgrade_plan("enterprise"): st.rerun()

    with tab3:
        st.subheader(tr("bus_brand_title"))
        if config.get("plan") not in ["enterprise", "pro"]:
            st.warning(tr("bus_brand_warn"))
        
        branding = config.get("branding", {})
        c_name = st.text_input(tr("bus_company_name"), value=branding.get("company_name", ""))
        c_theme = st.color_picker(tr("bus_theme_color"), value=branding.get("theme_color", "#000000"))
        
        if st.button(tr("bus_save_brand"), key="save_branding"):
            bc.update_branding(c_name, c_theme)
            log_admin_op("branding_update", {"company_name": c_name})
            st.success(tr("bus_save_success"))

def render_telegram_stats():
    """Telegram 统计界面"""
    st.subheader("📊 使用统计")
    
    # 读取统计数据
    try:
        import json
        from datetime import datetime
        import pandas as pd
        with open("platforms/telegram/stats.json", 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        # 计算成功率
        success_rate = 0
        if stats['total_replies'] > 0:
            success_rate = (stats['success_count'] / stats['total_replies']) * 100
        
        # 显示统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总消息数", stats['total_messages'])
        
        with col2:
            st.metric("总回复数", stats['total_replies'])
        
        with col3:
            st.metric("成功率", f"{success_rate:.1f}%")
        
        with col4:
            st.metric("失败次数", stats['error_count'])
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("私聊消息", stats['private_messages'])
        
        with col2:
            st.metric("群聊消息", stats['group_messages'])
        
        # 运行时间
        if stats.get('start_time'):
            start_time = datetime.fromisoformat(stats['start_time'])
            running_time = datetime.now() - start_time
            days = running_time.days
            hours = running_time.seconds // 3600
            minutes = (running_time.seconds % 3600) // 60
            
            st.divider()
            st.info(f"⏱️ 运行时长: {days}天 {hours}小时 {minutes}分钟")
        
        if stats.get('last_active'):
            # last_active = datetime.fromisoformat(stats['last_active'])
            # st.caption(f"最后活跃: {last_active.strftime('%Y-%m-%d %H:%M:%S')}")
            st.caption(tr("tg_stats_last_active").format(format_time(stats['last_active'])))
        
        # 审核与兜底趋势（最近 1000 行）
        try:
            audit_path = os.path.join("platforms", "telegram", "logs", "audit.log")
            fallback_count = 0
            pass_count = 0
            fail_count = 0
            if os.path.exists(audit_path):
                with open(audit_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                tail = lines[-1000:] if len(lines) > 1000 else lines
                for ln in tail:
                    if "Selected fallback message hash" in ln:
                        fallback_count += 1
                    if '"status": "PASS"' in ln or "'status': 'PASS'" in ln:
                        pass_count += 1
                    if '"status": "FAIL"' in ln or "'status': 'FAIL'" in ln:
                        fail_count += 1
            st.subheader("审核与兜底趋势")
            st.caption("统计最近 1000 行审核日志中的 PASS/FAIL/兜底触发次数")
            chart_df = pd.DataFrame({
                "类别": ["PASS", "FAIL", "兜底"],
                "次数": [pass_count, fail_count, fallback_count]
            })
            st.bar_chart(chart_df.set_index("类别"))
        except Exception as exc:
            st.warning(f"审核统计读取失败：{exc}")
        
        # 操作按钮
        if st.button("🗑️ 重置统计", use_container_width=True):
            default_stats = {
                "total_messages": 0,
                "total_replies": 0,
                "private_messages": 0,
                "group_messages": 0,
                "success_count": 0,
                "error_count": 0,
                "start_time": datetime.now().isoformat(),
                "last_active": None
            }
            with open("platforms/telegram/stats.json", 'w', encoding='utf-8') as f:
                json.dump(default_stats, f, indent=2, ensure_ascii=False)
            st.success("✅ 统计已重置")
            st.rerun()
        if st.button("刷新统计", use_container_width=True):
            st.rerun()
        
    except Exception as e:
        st.error(f"读取统计失败: {e}")
        st.info("💡 统计数据将在机器人运行后生成")

# ==================== WhatsApp 面板 ====================

def get_whatsapp_status():
    """获取 WhatsApp 机器人运行状态（支持租户隔离）"""
    tenant_id = st.session_state.get('tenant', 'default')
    # PID文件放在租户目录下
    pid_file = f"data/tenants/{tenant_id}/platforms/whatsapp/bot.pid"
    
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                import psutil
                if psutil.pid_exists(pid):
                    return True, pid
            except:
                pass
        return False, None
    except:
        return False, None

def start_whatsapp_bot():
    """启动 WhatsApp 机器人（支持租户隔离）"""
    tenant_id = st.session_state.get('tenant', 'default')
    
    try:
        # 检查 Node.js
        import subprocess
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            return False, tr("wa_err_no_node")
        
        # 检查依赖
        if not os.path.exists("platforms/whatsapp/node_modules"):
            return False, tr("wa_err_missing_deps")
        
        # 启动机器人
        whatsapp_dir = "platforms/whatsapp"
        
        # 租户隔离的日志和PID路径
        tenant_wa_dir = f"data/tenants/{tenant_id}/platforms/whatsapp"
        os.makedirs(tenant_wa_dir, exist_ok=True)
        
        log_file = os.path.join(tenant_wa_dir, "bot.log")
        pid_file = os.path.join(tenant_wa_dir, "bot.pid")
        
        # 清理旧文件（避免权限问题）
        try:
            if os.path.exists(log_file):
                os.remove(log_file)
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except:
            pass
        
        # 使用 'a' 模式而不是 'w'，避免权限问题
        log_handle = open(log_file, 'a', encoding='utf-8', buffering=1)
        
        # 传递租户上下文给 bot.js (通过环境变量)
        env = os.environ.copy()
        env['TENANT_ID'] = tenant_id
        
        if sys.platform == 'win32':
            process = subprocess.Popen(
                ['node', 'bot.js'],
                cwd=whatsapp_dir,
                env=env, # 注入环境变量
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                bufsize=1
            )
        else:
            process = subprocess.Popen(
                ['node', 'bot.js'],
                cwd=whatsapp_dir,
                env=env, # 注入环境变量
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        
        # 保存 PID 到租户目录
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(process.pid))
        
        # 注意：不要关闭 log_handle，让进程继续使用
        
        return True, tr("wa_start_success").format(process.pid)
    except Exception as e:
        return False, tr("wa_start_fail").format(str(e))

def stop_whatsapp_bot():
    """停止 WhatsApp 机器人（支持租户隔离）"""
    tenant_id = st.session_state.get('tenant', 'default')
    pid_file = f"data/tenants/{tenant_id}/platforms/whatsapp/bot.pid"
    
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r', encoding='utf-8') as f:
                pid = int(f.read().strip())
            
            import psutil
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
            
            os.remove(pid_file)
            return True, tr("wa_stop_success")
        else:
            return False, tr("wa_stop_not_running")
    except Exception as e:
        return False, tr("wa_stop_fail").format(str(e))

def render_whatsapp_panel():
    """WhatsApp 主面板"""
    st.header(f"💬 {tr('wa_header')}")
    _render_scope_hint("仅 WhatsApp 平台生效")
    
    # 检查是否有二维码需要显示
    qr_image_path = "platforms/whatsapp/qr_code.png"
    status_file_path = "platforms/whatsapp/login_status.json"
    
    # 显示二维码弹窗
    if os.path.exists(qr_image_path) and os.path.exists(status_file_path):
        try:
            import json
            with open(status_file_path, 'r', encoding='utf-8') as f:
                login_status = json.load(f)
            
            if login_status.get('status') == 'waiting' and login_status.get('qr_available'):
                with st.expander(f"📱 {tr('wa_qr_title')}", expanded=True):
                    st.info(tr('wa_qr_scan_hint'))
                    st.image(qr_image_path, caption=tr('wa_qr_caption'), width=400)
                    st.caption(tr('wa_qr_step1'))
                    st.caption(tr('wa_qr_step2'))
                    
                    if st.button(tr('wa_qr_refresh'), key="refresh_qr"):
                        st.rerun()
        except Exception as e:
            st.error(f"{tr('wa_status_read_err').format(e)}")
    
    # 状态显示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        is_running, pid = get_whatsapp_status()
        if is_running:
            st.success(f"{tr('wa_status_running')} (PID: {pid})")
        else:
            st.error(tr('wa_status_stopped'))
    
    with col2:
        if os.path.exists("platforms/whatsapp/.wwebjs_auth"):
            st.success(tr('tg_status_logged_in'))
        else:
            st.warning(tr('tg_status_not_logged_in'))
            if st.button("📲 去登录", key="wa_goto_login"):
                @st.dialog("WhatsApp 登录指南")
                def show_wa_login_guide():
                    st.markdown("""
                    ### 🚀 如何扫码登录？
                    
                    1. 点击下方的 **启动** 按钮启动机器人进程。
                    2. 等待几秒钟，上方会出现一个 **二维码** 面板。
                    3. 打开手机 WhatsApp -> 设置 -> 关联设备 -> 扫码。
                    
                    ---
                    **注意**: 扫码成功后，状态会自动变为 ✅ 已登录。
                    """)
                    if st.button("我已了解", type="primary"):
                        st.rerun()
                show_wa_login_guide()
    
    with col3:
        if os.path.exists(".env"):
            st.success(tr('tg_config_success'))
        else:
            st.error(tr('tg_config_missing'))
            if st.button("⚙️ 去配置", key="wa_goto_config"):
                @st.dialog("WhatsApp 初始化配置")
                def show_wa_config_guide():
                    st.markdown("""
                    ### 📝 配置文件缺失
                    
                    当前环境尚未配置 WhatsApp 必要参数。
                    
                    **解决方案**:
                    1. 切换到下方的 **⚙️ 功能配置** 标签页。
                    2. 确认人设 (Persona) 和关键词配置。
                    3. 点击 **💾 保存配置**。
                    
                    注意：WhatsApp 主要依赖 Node.js 环境和环境变量，请确保 `.env` 文件已在系统设置中生成。
                    """)
                    if st.button("前往系统设置", type="primary"):
                         st.session_state.current_page = "sys_config"
                         st.rerun()
                show_wa_config_guide()
    
    st.divider()
    
    # 控制按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(tr('wa_btn_start'), use_container_width=True, type="primary", 
                    disabled=is_running, key="whatsapp_start"):
            success, message = start_whatsapp_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button(tr('wa_btn_stop'), use_container_width=True, 
                    disabled=not is_running, key="whatsapp_stop"):
            success, message = stop_whatsapp_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col3:
        if st.button(tr('wa_btn_restart'), use_container_width=True,
                    disabled=not is_running, key="whatsapp_restart"):
            stop_whatsapp_bot()
            import time
            time.sleep(1)
            start_whatsapp_bot()
            st.success(tr('wa_restart_success'))
            st.rerun()
    
    st.divider()
    
    # Tab 界面
    tab1, tab2, tab3 = st.tabs([
        tr('tg_tab_config'), tr('tg_tab_logs'), tr('tg_tab_stats')
    ])
    
    with tab1:
        render_whatsapp_config()
    
    with tab2:
        render_whatsapp_logs()
    
    with tab3:
        render_whatsapp_stats()

# ==================== WhatsApp 租户级工具函数 ====================
def _get_tenant_wa_paths(tenant_id):
    base = f"data/tenants/{tenant_id}/platforms/whatsapp"
    return {
        "config": "platforms/whatsapp/config.txt", # read_tenant_file 会自动处理
        "prompt": "platforms/whatsapp/prompt.txt",
        "keywords": "platforms/whatsapp/keywords.txt",
        "log": os.path.join(base, "bot.log"),
        "stats": os.path.join(base, "stats.json")
    }

def render_whatsapp_config():
    """WhatsApp 配置界面 (多租户适配版)"""
    tenant_id = st.session_state.get('tenant', 'default')
    paths = _get_tenant_wa_paths(tenant_id)
    
    st.subheader(tr('wa_cfg_header'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{tr('wa_cfg_persona')}**")
        prompt = st.text_area(
            tr('wa_cfg_prompt_label'),
            value=read_tenant_file(paths["prompt"], "你是一个幽默的助手"),
            height=200,
            key="wa_prompt"
        )
        if st.button(tr('wa_cfg_save_prompt'), key="wa_save_prompt"):
            write_tenant_file(paths["prompt"], prompt)
            log_admin_op("wa_prompt_save", {"path": paths["prompt"], "tenant": tenant_id})
            st.success(tr('common_success'))
    
    with col2:
        st.markdown(f"**{tr('wa_cfg_keywords')}**")
        keywords = st.text_area(
            tr('wa_cfg_keywords_label'),
            value=read_tenant_file(paths["keywords"], "帮我\n求助\nAI"),
            height=200,
            key="wa_keywords"
        )
        if st.button(tr('wa_cfg_save_keywords'), key="wa_save_keywords"):
            write_tenant_file(paths["keywords"], keywords)
            log_admin_op("wa_keywords_save", {"path": paths["keywords"], "tenant": tenant_id})
            st.success(tr('common_success'))
    
    st.divider()
    
    st.markdown(f"**{tr('wa_cfg_switches')}**")
    config_content = read_tenant_file(paths["config"], "PRIVATE_REPLY=on\nGROUP_REPLY=on")
    
    col1, col2 = st.columns(2)
    
    with col1:
        private_reply = "on" if "PRIVATE_REPLY=on" in config_content else "off"
        private_enabled = st.toggle(tr('wa_cfg_private_reply'), value=(private_reply=="on"), key="wa_private")
    
    with col2:
        group_reply = "on" if "GROUP_REPLY=on" in config_content else "off"
        group_enabled = st.toggle(tr('wa_cfg_group_reply'), value=(group_reply=="on"), key="wa_group")
    
    if st.button(tr('wa_cfg_save_config'), key="wa_save_config"):
        new_config = f"PRIVATE_REPLY={'on' if private_enabled else 'off'}\nGROUP_REPLY={'on' if group_enabled else 'off'}"
        write_tenant_file(paths["config"], new_config)
        log_admin_op("wa_config_save", {"private_reply": private_enabled, "group_reply": group_enabled, "tenant": tenant_id})
        st.success(tr('common_success'))
    
    st.info(tr('wa_cfg_tip_restart'))

def render_whatsapp_logs():
    """WhatsApp 日志界面 (多租户适配版)"""
    st.subheader(tr('wa_log_header'))
    
    tenant_id = st.session_state.get('tenant', 'default')
    log_file = _get_tenant_wa_paths(tenant_id)["log"]
    
    # 兼容旧路径
    if tenant_id == 'default' and not os.path.exists(log_file) and os.path.exists("platforms/whatsapp/bot.log"):
        log_file = "platforms/whatsapp/bot.log"
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            last_modified = datetime.fromtimestamp(os.path.getmtime(log_file))
            st.caption(f"{tr('wa_log_file_size').format(file_size)} | {tr('wa_log_last_updated').format(format_time(last_modified))}")
    
    with col2:
        if st.button(tr('wa_log_refresh'), use_container_width=True, key="wa_refresh"):
            st.rerun()
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.read()
            
            if logs.strip():
                st.code(logs, language="log", line_numbers=False)
            else:
                st.info(tr('wa_log_empty'))
        else:
            st.warning(tr('wa_log_missing'))
    except Exception as e:
        st.error(tr('wa_log_read_err').format(e))
    
    if st.button(tr('wa_log_clear'), key="wa_clear"):
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'w') as f:
                f.write("")
            st.success(tr('wa_log_cleared'))
            st.rerun()
        except:
            st.error(tr('wa_log_clear_fail'))

def render_whatsapp_stats():
    """WhatsApp 统计界面 (多租户适配版)"""
    st.subheader(tr('wa_stats_header'))
    
    tenant_id = st.session_state.get('tenant', 'default')
    stats_file = _get_tenant_wa_paths(tenant_id)["stats"]
    
    # 兼容旧路径
    if tenant_id == 'default' and not os.path.exists(stats_file) and os.path.exists("platforms/whatsapp/stats.json"):
        stats_file = "platforms/whatsapp/stats.json"

    # 读取统计数据
    try:
        import json
        from datetime import datetime
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)

        
        # 计算成功率
        success_rate = 0
        if stats['total_replies'] > 0:
            success_rate = (stats['success_count'] / stats['total_replies']) * 100
        
        # 显示统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(tr('wa_stats_total_msgs'), stats['total_messages'])
        
        with col2:
            st.metric(tr('wa_stats_total_replies'), stats['total_replies'])
        
        with col3:
            st.metric(tr('wa_stats_success_rate'), f"{success_rate:.1f}%")
        
        with col4:
            st.metric(tr('wa_stats_failures'), stats['error_count'])
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(tr('wa_stats_private'), stats['private_messages'])
        
        with col2:
            st.metric(tr('wa_stats_group'), stats['group_messages'])
        
        # 运行时间
        if stats.get('start_time'):
            start_time = datetime.fromisoformat(stats['start_time'])
            running_time = datetime.now() - start_time
            days = running_time.days
            hours = running_time.seconds // 3600
            minutes = (running_time.seconds % 3600) // 60
            
            st.divider()
            st.info(tr('wa_stats_runtime').format(d=days, h=hours, m=minutes))
        
        if stats.get('last_active'):
            st.caption(tr('wa_stats_last_active').format(format_time(stats['last_active'])))
        
        # 重置按钮
        if st.button(tr('wa_stats_reset'), use_container_width=True, key="wa_reset_stats"):
            default_stats = {
                "total_messages": 0,
                "total_replies": 0,
                "private_messages": 0,
                "group_messages": 0,
                "success_count": 0,
                "error_count": 0,
                "start_time": datetime.now().isoformat(),
                "last_active": None
            }
            with open("platforms/whatsapp/stats.json", 'w', encoding='utf-8') as f:
                json.dump(default_stats, f, indent=2, ensure_ascii=False)
            st.success(tr('wa_stats_reset_success'))
            st.rerun()
        
    except Exception as e:
        st.error(tr('wa_stats_read_err').format(e))
        st.info(tr('wa_stats_wait'))

def render_coming_soon_panel(platform_name, platform_info):
    """渲染开发中的平台面板"""
    st.header(f"{platform_info['icon']} {platform_name} - 开发中")
    
    st.info(f"""
    ### 🚧 平台开发中
    
    **{platform_name}** 功能正在开发中，敬请期待！
    
    **计划功能：**
    - ✅ 自动回复
    - ✅ 上下文记忆
    - ✅ 群发消息
    - ✅ Web 管理
    - ✅ 统计报表
    
    **预计上线：** 待定
    
    ---
    
    💡 如果你急需此平台支持，请联系开发者。
    """)
    
    # 开发进度
    st.markdown("### 📈 开发进度")
    
    progress_data = {
        'whatsapp': 30,
        'facebook': 10,
        'messenger': 10,
        'wechat': 5,
        'instagram': 5,
        'twitter': 5,
        'discord': 5
    }
    
    progress = progress_data.get(platform_info.get('id', ''), 0)
    st.progress(progress / 100)
    st.caption(f"完成度: {progress}%")

def render_audit_panel():
    from keyword_manager import KeywordManager
    st.header(tr("audit_header"))
    _render_scope_hint("全平台生效（可对各平台单独开关）")
    
    # 权限校验：仅审核员可访问此模块。请在左侧切换身份为 Auditor。
    role = st.session_state.get('user_role', 'SuperAdmin')
    if role != 'Auditor' and role != 'SuperAdmin':
        st.warning(tr("audit_role_warn"))
        return
    
    # Init manager
    km = KeywordManager()
    
    tab1, tab2, tab3 = st.tabs([tr("audit_tab_keywords"), tr("audit_tab_logs"), tr("audit_tab_config")])
    
    with tab1:
        st.subheader(tr("audit_tab_keywords"))
        st.info(tr("audit_kw_info"))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(tr("audit_block_header"))
            st.caption(tr("audit_block_caption"))
            keywords = km.get_keywords().get('block', [])
            
            # Display stats
            st.write(tr("audit_block_count").format(len(keywords)))
            
            # Add new
            new_block = st.text_input(tr("audit_block_add"), key="new_block_input")
            if st.button(tr("audit_block_add_btn"), key="add_block_btn"):
                if new_block:
                    success, msg = km.add_keyword('block', new_block)
                    if success: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            
            # Remove
            if keywords:
                to_remove = st.selectbox(tr("audit_block_del_sel"), [""] + keywords, key="del_block_sel")
                if st.button(tr("audit_block_del_btn"), key="del_block_btn"):
                    if to_remove:
                        km.remove_keyword('block', to_remove)
                        st.success(f"{tr('common_delete')} {to_remove}")
                        st.rerun()
            
            # Rename
            if keywords:
                col_rename_b1, col_rename_b2 = st.columns([1, 1])
                with col_rename_b1:
                    to_rename = st.selectbox(tr("audit_block_rename_sel"), [""] + keywords, key="rename_block_sel")
                with col_rename_b2:
                    new_name = st.text_input(tr("tg_kw_new_name"), key="rename_block_new")
                if st.button(tr("tg_kw_rename"), key="rename_block_btn"):
                    if to_rename and new_name:
                        ok, msg = km.rename_keyword('block', to_rename, new_name)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
            
            # List all (Tag style)
            st.markdown("---")
            st.markdown(" ".join([f"`{k}`" for k in keywords]))

        with col2:
            st.markdown(tr("audit_sens_header"))
            st.caption(tr("audit_sens_caption"))
            keywords = km.get_keywords().get('sensitive', [])
            
            st.write(tr("audit_sens_count").format(len(keywords)))
            
            new_sens = st.text_input(tr("tg_kw_add"), key="new_sens_input")
            if st.button(tr("tg_kw_add"), key="add_sens_btn"):
                if new_sens:
                    success, msg = km.add_keyword('sensitive', new_sens)
                    if success: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            
            if keywords:
                to_remove_sens = st.selectbox(tr("tg_kw_del"), [""] + keywords, key="del_sens_sel")
                if st.button(tr("tg_kw_del"), key="del_sens_btn"):
                    if to_remove_sens:
                        km.remove_keyword('sensitive', to_remove_sens)
                        st.success(f"{tr('common_delete')} {to_remove_sens}")
                        st.rerun()
            
            # Rename
            if keywords:
                col_rename_s1, col_rename_s2 = st.columns([1, 1])
                with col_rename_s1:
                    to_rename_s = st.selectbox(tr("tg_kw_rename"), [""] + keywords, key="rename_sens_sel")
                with col_rename_s2:
                    new_name_s = st.text_input(tr("tg_kw_new_name"), key="rename_sens_new")
                if st.button(tr("tg_kw_rename"), key="rename_sens_btn"):
                    if to_rename_s and new_name_s:
                        ok, msg = km.rename_keyword('sensitive', to_rename_s, new_name_s)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
            
            st.markdown("---")
            st.markdown(" ".join([f"`{k}`" for k in keywords]))

        st.divider()
        st.markdown(tr("audit_allow_header"))
        allow_list = km.get_keywords().get('allow', [])
        st.write(tr("audit_allow_count").format(len(allow_list)))
        new_allow = st.text_input(tr("tg_kw_add"), key="new_allow_input")
        if st.button(tr("tg_kw_add"), key="add_allow_btn"):
            if new_allow:
                success, msg = km.add_keyword('allow', new_allow)
                if success: st.success(msg)
                else: st.warning(msg)
                st.rerun()
        if allow_list:
            to_remove_allow = st.selectbox(tr("tg_kw_del"), [""] + allow_list, key="del_allow_sel")
            if st.button(tr("tg_kw_del"), key="del_allow_btn"):
                if to_remove_allow:
                    km.remove_keyword('allow', to_remove_allow)
                    st.success(f"{tr('common_delete')} {to_remove_allow}")
                    st.rerun()
            col_rename_a1, col_rename_a2 = st.columns([1, 1])
            with col_rename_a1:
                to_rename_allow = st.selectbox(tr("tg_kw_rename"), [""] + allow_list, key="rename_allow_sel")
            with col_rename_a2:
                new_name_allow = st.text_input(tr("tg_kw_new_name"), key="rename_allow_new")
            if st.button(tr("tg_kw_rename"), key="rename_allow_btn"):
                if to_rename_allow and new_name_allow:
                    ok, msg = km.rename_keyword('allow', to_rename_allow, new_name_allow)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
        st.markdown("---")
        st.markdown(" ".join([f"`{k}`" for k in allow_list]))

    with tab2:
        st.subheader(tr("audit_tab_logs"))
        # 从数据库加载日志
        tenant_id = st.session_state.get("tenant", "default")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(tr("audit_log_refresh"), key="audit_log_refresh"):
                st.rerun()
        
        # 优先使用数据库
        try:
            logs_data = db.get_audit_logs(tenant_id, limit=100)
            if logs_data:
                # 转换为 DataFrame 展示
                import pandas as pd
                df = pd.DataFrame(logs_data)
                # 格式化时间
                if 'timestamp' in df.columns:
                    df['timestamp'] = df['timestamp'].apply(lambda x: format_time(x) if x else x)
                # 重命名列
                df = df.rename(columns={
                    "timestamp": tr("audit_log_col_time"),
                    "user_role": tr("audit_log_col_role"),
                    "action": tr("audit_log_col_action"),
                    "details": tr("audit_log_col_details")
                })
                # 选择展示列
                cols_to_show = [c for c in [tr("audit_log_col_time"), tr("audit_log_col_role"), tr("audit_log_col_action"), tr("audit_log_col_details")] if c in df.columns]
                st.dataframe(df[cols_to_show], use_container_width=True)
            else:
                st.info(tr("audit_log_no_data"))
        except Exception as e:
            st.error(tr("audit_db_err").format(e))
            # Fallback to file
            log_file = os.path.join("platforms", "telegram", "logs", "audit.log")
            if os.path.exists(log_file):
                logs = read_log_file(log_file, 50)
                st.code(logs, language="text")

    with tab3:
        st.subheader(tr("audit_tab_config"))
        
        # 读取当前配置
        config_path = os.path.join("platforms", "telegram", "config.txt")
        current_config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        try:
                            k, v = line.strip().split("=", 1)
                            current_config[k.strip()] = v.strip()
                        except:
                            pass
        
        # 权限控制
        can_edit = (st.session_state.get("user_role") == "SuperAdmin")
        if not can_edit:
            st.info("当前为只读视图，切换到 SuperAdmin 可编辑配置")
        
        # 1. 启用开关（全局 + 平台差异化）
        audit_enabled = current_config.get("AUDIT_ENABLED", "True") == "True"
        new_enabled = st.toggle(tr("audit_cfg_enable"), value=audit_enabled, disabled=not can_edit)
        tg_enabled = current_config.get("TG_AUDIT_ENABLED", "True") == "True"
        wa_enabled = current_config.get("WA_AUDIT_ENABLED", "False") == "True"
        colA, colB = st.columns(2)
        with colA:
            new_tg_enabled = st.toggle("Telegram 审核开关", value=tg_enabled, disabled=not can_edit)
        with colB:
            new_wa_enabled = st.toggle("WhatsApp 审核开关", value=wa_enabled, disabled=not can_edit)
        
        # 2. 模式与远程服务器
        audit_mode = current_config.get("AUDIT_MODE", "local")
        mode_opt = st.selectbox("审核模式", ["local", "remote", "dual"], index=["local","remote","dual"].index(audit_mode), disabled=not can_edit)
        
        audit_servers = current_config.get("AUDIT_SERVERS", "")
        new_servers = st.text_input(tr("audit_cfg_url"), value=audit_servers, help=tr("audit_cfg_remote_help"), disabled=not can_edit)
        
        # 3. 风格守卫强度与敏感词库版本
        strength = float(current_config.get("AUDIT_GUIDE_STRENGTH", "0.7"))
        new_strength = st.slider("拦截规则强度", min_value=0.0, max_value=1.0, value=strength, step=0.1, disabled=not can_edit)
        dict_ver = current_config.get("SENSITIVE_DICT_VERSION", "v1")
        new_dict_ver = st.selectbox("敏感词库版本", ["v1","v2","v3"], index=["v1","v2","v3"].index(dict_ver), disabled=not can_edit)
        
        # 4. 定时生效规则
        start_time = current_config.get("AUDIT_ACTIVE_START", "")
        end_time = current_config.get("AUDIT_ACTIVE_END", "")
        colC, colD = st.columns(2)
        with colC:
            new_start = st.text_input("生效开始时间(ISO)", value=start_time, placeholder="2026-01-08T09:00:00", disabled=not can_edit)
        with colD:
            new_end = st.text_input("生效结束时间(ISO)", value=end_time, placeholder="2026-01-08T18:00:00", disabled=not can_edit)
        
        # 5. 黑白名单管理（复用现有组件或简化）
        st.caption("黑白名单管理请前往关键字管理页面进行维护")
        
        # 6. 配置导入/导出
        exp_dir = os.path.join(_ensure_data_dirs(), "config")
        os.makedirs(exp_dir, exist_ok=True)
        colX, colY = st.columns(2)
        with colX:
            if st.button("导出配置为JSON", disabled=not can_edit):
                export_path = os.path.join(exp_dir, "audit_config_export.json")
                try:
                    with open(export_path, "w", encoding="utf-8") as f:
                        json.dump(current_config, f, ensure_ascii=False, indent=2)
                    log_admin_op("audit_config_export", {"file": export_path})
                    st.success(f"已导出到: {export_path}")
                except Exception as e:
                    st.error(f"导出失败: {e}")
        with colY:
            imp_path = st.text_input("从JSON导入路径", value="", disabled=not can_edit)
            if st.button("导入配置", disabled=not can_edit):
                try:
                    if imp_path and os.path.exists(imp_path):
                        with open(imp_path, "r", encoding="utf-8") as f:
                            imported = json.load(f)
                        if isinstance(imported, dict):
                            current_config.update(imported)
                            log_admin_op("audit_config_import", {"file": imp_path})
                            st.success("已导入配置（需点击保存以生效）")
                        else:
                            st.error("导入内容格式错误")
                    else:
                        st.error("文件不存在")
                except Exception as e:
                    st.error(f"导入失败: {e}")
        
        st.divider()
        # 7. 配置备份与回滚
        def _archive_config(src):
            try:
                arc_dir = os.path.join("platforms","telegram","logs","archive")
                os.makedirs(arc_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = os.path.join(arc_dir, f"config_{ts}.txt")
                if os.path.exists(src):
                    import shutil
                    shutil.copy2(src, dest)
                    return dest
            except Exception:
                return None
        colE, colF = st.columns(2)
        with colE:
            if st.button("备份当前配置", disabled=not can_edit):
                archived = _archive_config(config_path)
                if archived:
                    log_admin_op("audit_config_backup", {"file": archived})
                    st.success(f"已备份到: {archived}")
                else:
                    st.warning("备份失败或源文件不存在")
        with colF:
            rollback_target = st.text_input("回滚目标路径", value="", disabled=not can_edit)
            if st.button("回滚到目标文件", disabled=not can_edit):
                try:
                    if rollback_target and os.path.exists(rollback_target):
                        import shutil
                        shutil.copy2(rollback_target, config_path)
                        log_admin_op("audit_config_rollback", {"file": rollback_target})
                        st.success("已回滚")
                        st.rerun()
                    else:
                        st.error("目标文件不存在")
                except Exception as e:
                    st.error(f"回滚失败: {e}")
        
        # 二次验证机制（简单验证码）
        if "cfg_confirm_code" not in st.session_state:
            import random
            st.session_state.cfg_confirm_code = str(random.randint(100000, 999999))
        st.info(f"确认码: {st.session_state.cfg_confirm_code} （保存前需输入）")
        confirm_input = st.text_input("输入确认码", value="", disabled=not can_edit)
        can_save = can_edit and (confirm_input.strip() == st.session_state.cfg_confirm_code)
        
        if st.button(tr("audit_cfg_save"), key="save_audit_config", disabled=not can_save):
            # 更新配置
            current_config["AUDIT_ENABLED"] = str(new_enabled)
            current_config["TG_AUDIT_ENABLED"] = str(new_tg_enabled)
            current_config["WA_AUDIT_ENABLED"] = str(new_wa_enabled)
            current_config["AUDIT_MODE"] = mode_opt
            current_config["AUDIT_SERVERS"] = new_servers
            current_config["AUDIT_GUIDE_STRENGTH"] = str(new_strength)
            current_config["SENSITIVE_DICT_VERSION"] = new_dict_ver
            current_config["AUDIT_ACTIVE_START"] = new_start
            current_config["AUDIT_ACTIVE_END"] = new_end
            try:
                log_admin_op("audit_config_save", {
                    "enabled": bool(new_enabled),
                    "mode": mode_opt,
                    "servers": new_servers,
                    "strength": new_strength,
                    "dict_version": new_dict_ver,
                    "tg_enabled": bool(new_tg_enabled),
                    "wa_enabled": bool(new_wa_enabled),
                    "active_start": new_start,
                    "active_end": new_end
                })
            except Exception:
                pass
            
            # 写入文件
            try:
                # 读取原文件保留注释
                lines = []
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                
                # 更新或添加
                updated_keys = set()
                new_lines = []
                for line in lines:
                    if "=" in line and not line.strip().startswith("#"):
                        key = line.split("=", 1)[0].strip()
                        if key in current_config:
                            new_lines.append(f"{key}={current_config[key]}\n")
                            updated_keys.add(key)
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                # 添加新key
                for k, v in current_config.items():
                    if k not in updated_keys:
                        new_lines.append(f"{k}={v}\n")
                
                with open(config_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                
                st.success(tr("tg_config_success"))
            except Exception as e:
                st.error(tr("audit_save_err").format(e))

def render_help_center():
    st.header("🆘 帮助中心")
    _render_scope_hint("全平台生效（只读文档）")
    
    # Path to docs
    docs_root = os.path.join(BASE_DIR, "docs", "help_center", "v1.0")
    lang = st.session_state.get("lang", "zh")
    lang_dir = "zh_CN" if lang == "zh" else "en_US" # Fallback logic
    if not os.path.exists(os.path.join(docs_root, lang_dir)):
        lang_dir = "zh_CN" # Default to ZH
        
    current_dir = os.path.join(docs_root, lang_dir)
    
    if not os.path.exists(current_dir):
        st.warning(f"文档目录不存在: {current_dir}")
        return

    # List MD files
    files = [f for f in os.listdir(current_dir) if f.endswith(".md")]
    files.sort()
    
    # 使用侧边栏已选择的“文档与目录”项
    selected_doc = st.session_state.get("doc_selector") or (files[0] if files else None)
    if selected_doc:
        file_path = os.path.join(current_dir, selected_doc)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split content to find mermaid blocks
        parts = content.split("```mermaid")
        
        for i, part in enumerate(parts):
            if i == 0:
                st.markdown(part)
            else:
                # This part starts with mermaid code, ends with ``` and then text
                subparts = part.split("```", 1)
                mermaid_code = subparts[0]
                remaining_text = subparts[1] if len(subparts) > 1 else ""
                
                # Render Mermaid using custom iframe to avoid Streamlit's default feature policy warnings
                import base64
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="utf-8">
                <style>
                body {{ margin: 0; background: white; }}
                .mermaid {{ padding: 10px; border-radius: 5px; overflow: auto; }}
                </style>
                </head>
                <body>
                <div class="mermaid">
                {mermaid_code}
                </div>
                <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true }});
                </script>
                </body>
                </html>
                """
                b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
                st.markdown(
                    f'<iframe src="data:text/html;base64,{b64}" width="100%" height="600" frameborder="0" style="background: white; border-radius: 5px;"></iframe>', 
                    unsafe_allow_html=True
                )
                
                st.markdown(remaining_text)

def render_test_cases_panel():
    st.header("🧪 测试用例集")
    _render_scope_hint("全平台生效（开发/运维回归）")

    tests_dir = os.path.join(BASE_DIR, "tests")
    if not os.path.exists(tests_dir):
        st.error(f"测试目录不存在: {tests_dir}")
        return

    known = [
        ("diagnostic_check.py", "环境/依赖诊断"),
        ("smoke_test_v2.py", "核心流程冒烟测试"),
        ("run_acceptance.py", "自动化验收测试"),
        ("user_acceptance_test.py", "用户验收脚本"),
        ("test_upgrade_flow.py", "升级流程回归"),
        ("test_dual_audit.py", "双层审核回归"),
        ("test_orchestrator.py", "编排逻辑回归"),
        ("test_kb.py", "知识库回归"),
        ("test_keyword_manager.py", "关键词管理回归"),
        ("test_platform_toggle.py", "平台开关回归"),
    ]
    existing_files = {f for f in os.listdir(tests_dir) if f.endswith(".py")}
    options = [(fname, title) for fname, title in known if fname in existing_files]
    if not options:
        st.warning("未发现可运行的测试脚本。")
        return

    def _run_script(script_file: str):
        import subprocess
        import time

        path = os.path.join(tests_dir, script_file)
        start = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, path],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=60 * 30
            )
            elapsed = time.time() - start
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "elapsed": elapsed,
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or ""
            }
        except subprocess.TimeoutExpired as e:
            elapsed = time.time() - start
            return {
                "ok": False,
                "returncode": None,
                "elapsed": elapsed,
                "stdout": e.stdout or "",
                "stderr": (e.stderr or "") + "\n[超时] 脚本运行超过限制时间"
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "ok": False,
                "returncode": None,
                "elapsed": elapsed,
                "stdout": "",
                "stderr": f"[异常] {e}"
            }

    st.subheader("一键回归")
    if st.button("运行推荐回归集", type="primary", width="stretch", key="tc_run_recommended"):
        run_list = [f for f, _ in options if f in {"diagnostic_check.py", "smoke_test_v2.py", "run_acceptance.py"}]
        if not run_list:
            st.warning("推荐回归集脚本不存在。")
        else:
            results = []
            with st.spinner("正在执行回归脚本，请稍候..."):
                for f in run_list:
                    r = _run_script(f)
                    results.append((f, r))
            option_map = {f: t for f, t in options}
            for f, r in results:
                title = option_map.get(f, f)
                status = "✅ 通过" if r["ok"] else "❌ 失败"
                st.markdown(f"**{status}** - {title}（{f}，耗时 {r['elapsed']:.1f}s）")
                if r["stdout"].strip():
                    st.code(r["stdout"], language="text")
                if r["stderr"].strip():
                    st.code(r["stderr"], language="text")

    st.divider()
    st.subheader("单脚本执行")
    choice = st.selectbox("选择脚本", options, format_func=lambda x: f"{x[1]}（{x[0]}）", key="tc_script_select")
    if st.button("运行所选脚本", use_container_width=True, key="tc_run_one"):
        fname = choice[0]
        with st.spinner(f"正在执行 {fname}..."):
            r = _run_script(fname)
        if r["ok"]:
            st.success(f"通过（耗时 {r['elapsed']:.1f}s）")
        else:
            st.error(f"失败（返回码 {r['returncode']}，耗时 {r['elapsed']:.1f}s）")
        if r["stdout"].strip():
            st.code(r["stdout"], language="text")
        if r["stderr"].strip():
            st.code(r["stderr"], language="text")

def _get_client_ip() -> str:
    ip = "unknown"
    try:
        ctx = getattr(st, "context", None)
        headers = getattr(ctx, "headers", None) if ctx else None
        if headers:
            xff = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
            if xff:
                ip = xff.split(",")[0].strip()
            xri = headers.get("x-real-ip") or headers.get("X-Real-IP")
            if ip == "unknown" and xri:
                ip = str(xri).strip()
    except Exception:
        pass
    return ip

def _ensure_auth_manager():
    if "auth" not in st.session_state:
        st.session_state.auth = AuthManager(db)

def _ensure_default_super_admin():
    try:
        users = db.list_users()
    except Exception:
        users = []
    if users:
        return
    _ensure_auth_manager()
    st.session_state.auth.create_user("admin", "admin123", "super_admin", None)

def _check_ip_whitelist_or_stop():
    ip = _get_client_ip()
    try:
        rows = db.list_ip_whitelist()
    except Exception:
        rows = []
    active_ips = []
    for r in rows or []:
        try:
            if int(r.get("is_active", 1) or 0) == 1:
                active_ips.append(r.get("ip_address"))
        except Exception:
            continue
    active_ips = [x for x in active_ips if x]
    if active_ips and ip not in active_ips:
        st.error("当前IP未在白名单中，禁止访问。")
        st.stop()

def _normalize_role(db_role: str) -> str:
    if (db_role or "").lower() == "super_admin":
        return "SuperAdmin"
    return "BusinessAdmin"

def _logout_system_user():
    for k in ["sys_user", "sys_logged_in", "user_role", "tenant"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

def _render_system_login():
    _check_ip_whitelist_or_stop()
    _ensure_auth_manager()
    _ensure_default_super_admin()

    st.markdown('<div class="main-header">👑鼎盛👑内部工具</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.subheader("系统登录")
        with st.form("sys_login_form"):
            username = st.text_input("账号")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录", use_container_width=True)
        if submitted:
            ip = _get_client_ip()
            user = st.session_state.auth.login(username, password, ip_address=ip)
            if not user:
                st.error("账号或密码错误，或账号已被禁用。")
                st.stop()
            role = _normalize_role(user.get("role"))
            if role == "BusinessAdmin" and not user.get("tenant_id"):
                st.error("业务管理员未绑定租户，无法登录。")
                st.stop()
            st.session_state.sys_user = user
            st.session_state.sys_logged_in = True
            st.session_state.user_role = role
            if role == "BusinessAdmin":
                st.session_state.tenant = user.get("tenant_id")
            else:
                if "tenant" not in st.session_state:
                    st.session_state.tenant = "default"
            st.rerun()

def _require_system_login():
    if not st.session_state.get("sys_logged_in"):
        _render_system_login()
        st.stop()
    _check_ip_whitelist_or_stop()

def _get_system_status():
    try:
        import psutil
    except Exception:
        return None
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        drive = os.path.splitdrive(os.path.abspath(os.getcwd()))[0] or "C:"
        disk = psutil.disk_usage(drive + "\\")
        return {
            "cpu": cpu_percent,
            "memory_used": mem.used / (1024 ** 3),
            "memory_total": mem.total / (1024 ** 3),
            "disk_used": disk.used / (1024 ** 3),
            "disk_total": disk.total / (1024 ** 3),
        }
    except Exception:
        return None

def render_system_admin_panel():
    st.header("🛠️ 系统管理")
    _ensure_auth_manager()

    tabs = st.tabs(["👥 租户与系统账号", "🛡️ IP白名单", "📜 登录日志", "📈 系统状态", "🚀 系统升级"])

    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("租户")
            tenants = []
            try:
                tenants = db.list_tenants() or []
            except Exception as e:
                st.error(str(e))
            if tenants:
                st.dataframe(tenants, use_container_width=True, hide_index=True)
            with st.expander("创建租户"):
                with st.form("sys_new_tenant"):
                    tid = st.text_input("Tenant ID")
                    plan = st.selectbox("Plan", ["free", "standard", "enterprise"])
                    ok = st.form_submit_button("创建", use_container_width=True)
                if ok:
                    if not tid:
                        st.error("Tenant ID 不能为空。")
                    else:
                        try:
                            db.create_tenant(tid, plan)
                            st.success("已创建租户。")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
        with c2:
            st.subheader("系统账号")
            users = []
            try:
                users = db.list_users() or []
            except Exception as e:
                st.error(str(e))
            if users:
                st.dataframe(users, use_container_width=True, hide_index=True)
            with st.expander("创建系统账号"):
                try:
                    tenants = db.list_tenants() or []
                except Exception:
                    tenants = []
                tenant_opts = [t.get("id") for t in tenants if t.get("id")]
                with st.form("sys_new_user"):
                    uname = st.text_input("账号名")
                    upass = st.text_input("密码", type="password")
                    urole = st.selectbox("角色", ["business_admin", "super_admin"])
                    utenant = st.selectbox("绑定租户", [""] + tenant_opts)
                    ok = st.form_submit_button("创建", use_container_width=True)
                if ok:
                    if not uname or not upass:
                        st.error("账号名/密码不能为空。")
                    elif urole == "business_admin" and not utenant:
                        st.error("业务管理员必须绑定租户。")
                    else:
                        ok2, msg = st.session_state.auth.create_user(uname, upass, urole, utenant if utenant else None)
                        if ok2:
                            st.success("已创建账号。")
                            st.rerun()
                        else:
                            st.error(str(msg))

    with tabs[1]:
        st.subheader("IP白名单")
        ips = []
        try:
            ips = db.list_ip_whitelist() or []
        except Exception as e:
            st.error(str(e))
        if ips:
            st.dataframe(ips, use_container_width=True, hide_index=True)

        with st.form("sys_add_ip"):
            c1, c2 = st.columns(2)
            ip_addr = c1.text_input("IP地址")
            ip_desc = c2.text_input("描述")
            ok = st.form_submit_button("加入白名单", use_container_width=True)
        if ok:
            try:
                db.add_ip_whitelist(ip_addr, ip_desc)
                st.success("已加入白名单。")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        if ips:
            del_ids = [str(r.get("id")) for r in ips if r.get("id") is not None]
            if del_ids:
                sel = st.selectbox("选择要删除的记录ID", del_ids)
                if st.button("删除选中记录", use_container_width=True):
                    try:
                        db.delete_ip_whitelist(int(sel))
                        st.success("已删除。")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[2]:
        st.subheader("系统用户登录日志")
        try:
            logs = db.get_login_history(limit=200) or []
        except Exception as e:
            logs = []
            st.error(str(e))
        if logs:
            st.dataframe(logs, use_container_width=True, hide_index=True)
        else:
            st.info("暂无登录日志。")

    with tabs[3]:
        st.subheader("系统运行状态")
        if st.button("刷新", use_container_width=True):
            st.rerun()
        status = _get_system_status()
        if not status:
            st.warning("无法获取系统状态。")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("CPU 使用率", f"{status['cpu']}%")
            c2.metric("内存", f"{status['memory_used']:.1f} / {status['memory_total']:.1f} GB")
            c3.metric("磁盘", f"{status['disk_used']:.1f} / {status['disk_total']:.1f} GB")
            st.progress(min(max(status["cpu"] / 100, 0.0), 1.0), text="CPU")
            st.progress(min(max(status["memory_used"] / status["memory_total"], 0.0), 1.0), text="内存")

    with tabs[4]:
        st.subheader("系统升级")
        st.info(f"当前版本: {APP_VERSION}")
        if st.button("检查更新", use_container_width=True):
            st.success("已是最新版本。")

def main():
    if 'show_login_panel' not in st.session_state:
        st.session_state.show_login_panel = False

    """主函数"""
    _require_system_login()
    st.markdown('<div class="main-header">👑鼎盛👑内部工具</div>', unsafe_allow_html=True)

    if 'lang' not in st.session_state:
        st.session_state.lang = 'zh'
    if 'tenant' not in st.session_state:
        st.session_state.tenant = 'default'

    sys_user = st.session_state.get("sys_user") or {}
    st.sidebar.markdown("### 👤 当前登录")
    st.sidebar.caption(f"账号: {sys_user.get('username', '-')}")
    st.sidebar.caption(f"角色: {st.session_state.get('user_role', '-')}")
    if sys_user.get("tenant_id"):
        st.sidebar.caption(f"租户: {sys_user.get('tenant_id')}")
    if st.sidebar.button("退出登录", use_container_width=True):
        _logout_system_user()

    # st.sidebar.markdown("### 👤 身份切换")
    # st.sidebar.caption("当前系统仅支持 superAdmin 权限")
    # st.sidebar.divider()
    st.sidebar.markdown(f"### 🌐 {tr('nav_lang')}")
    lang_disp = st.sidebar.selectbox(tr("nav_lang"), [LANGS["zh"], LANGS["en"]], key="lang_selector")
    st.session_state.lang = "zh" if lang_disp == LANGS["zh"] else "en"
    
    st.sidebar.markdown(f"### 🕒 {tr('nav_timezone')}")
    common_timezones = ["UTC", "Asia/Shanghai", "Asia/Hong_Kong", "Asia/Tokyo", "Asia/Singapore", "America/New_York", "Europe/London", "Europe/Paris", "Australia/Sydney"]
    if 'timezone' not in st.session_state:
        st.session_state.timezone = "Asia/Shanghai"
    
    tz_idx = 0
    if st.session_state.timezone in common_timezones:
        tz_idx = common_timezones.index(st.session_state.timezone)
        
    st.session_state.timezone = st.sidebar.selectbox(tr("nav_timezone"), common_timezones, index=tz_idx, key="timezone_selector")

    st.sidebar.markdown(f"### 🏷️ {tr('nav_tenant')}")
    if st.session_state.get("user_role") == "BusinessAdmin":
        st.sidebar.text_input("租户ID", value=st.session_state.tenant, key="tenant_input", disabled=True)
    else:
        st.session_state.tenant = st.sidebar.text_input("租户ID", value=st.session_state.tenant, key="tenant_input")
    
    # ----------------------
    
    # 初始化 session state
    if 'selected_platform' not in st.session_state:
        st.session_state.selected_platform = 'telegram'
    
    # 左侧平台选择器
    selected_platform = render_platform_selector()

    current_role = st.session_state.get("user_role", "SuperAdmin")
    platform_info = PLATFORMS.get(selected_platform, {})
    allowed_roles = platform_info.get("roles")
    if allowed_roles and current_role not in allowed_roles:
        fallback = None
        for pid, info in PLATFORMS.items():
            if info.get("status") != "available":
                continue
            roles = info.get("roles")
            if roles and current_role not in roles:
                continue
            fallback = pid
            break
        if fallback:
            st.session_state.selected_platform = fallback
        st.rerun()
    
    # 侧边栏底部信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 系统信息")
    st.sidebar.caption(f"版本: {APP_VERSION}")
    st.sidebar.caption(f"Python: {sys.version.split()[0]}")
    st.sidebar.caption(f"Streamlit: {st.__version__}")
    
    # 右侧主面板
    platform_info = PLATFORMS[selected_platform]
    
    if platform_info['status'] == 'available':
        if selected_platform == 'knowledge':
            render_kb_panel()
        elif selected_platform == 'ai_learning':
            render_ai_learning_panel()
        elif selected_platform == 'skills':
            render_skills_panel()
        elif selected_platform == 'audit':
            render_audit_panel()
        elif selected_platform == 'business':
            render_business_panel()
        elif selected_platform == 'accounts':
            render_accounts_panel()
        elif selected_platform == 'ai_config':
            render_ai_config_panel()
        elif selected_platform == 'api_gateway':
            render_api_gateway_panel()
        elif selected_platform == 'sys_config':
            render_sys_config_panel()
        elif selected_platform == 'system_admin':
            render_system_admin_panel()
        elif selected_platform == 'telegram':
            render_telegram_panel()
        elif selected_platform == 'whatsapp':
            render_whatsapp_panel()
        elif selected_platform == 'orchestrator':
            render_orchestrator_panel()
        elif selected_platform == 'supervisor':
            render_supervisor_panel()
        elif selected_platform == 'help_center':
            render_help_center()
        elif selected_platform == 'system_status':
            render_system_status_panel()
        elif selected_platform == 'test_cases':
            render_test_cases_panel()
        else:
            render_coming_soon_panel(platform_info['name'], {**platform_info, 'id': selected_platform})
    else:
        render_coming_soon_panel(platform_info['name'], {**platform_info, 'id': selected_platform})
    
    # 页脚
    st.markdown("---")
    st.caption("💡 提示：点击左侧选择不同的社交媒体平台")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        st.error(f"❌ 程序错误: {e}")
        import traceback
        st.code(traceback.format_exc())
