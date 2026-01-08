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
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 页面配置
st.set_page_config(
    page_title="👑鼎盛👑内部工具",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 样式（优化紧凑版）
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
    }
    .platform-card {
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        margin: 0.3rem 0;
        transition: all 0.3s;
    }
    .platform-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .platform-active {
        border-color: #1f77b4 !important;
        background-color: #f0f8ff;
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: bold;
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
    /* 紧凑侧边栏样式 */
    [data-testid="stSidebar"] {
        padding-top: 2rem;
    }
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.3rem;
    }
    [data-testid="stSidebar"] button {
        padding: 0.3rem 0.5rem;
        font-size: 0.85rem;
    }
    [data-testid="stSidebar"] small {
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# 平台配置
PLATFORMS = {
    'telegram': {
        'name': 'Telegram',
        'icon': '📱',
        'color': '#0088cc',
        'status': 'available',  # available, unavailable, coming_soon
        'description': '全功能支持 - 私聊/群聊/频道'
    },
    'whatsapp': {
        'name': 'WhatsApp',
        'icon': '💬',
        'color': '#25D366',
        'status': 'available',
        'description': '✅ 可用 - 私聊/群聊自动回复'
    },
    'facebook': {
        'name': 'Facebook',
        'icon': '📘',
        'color': '#1877f2',
        'status': 'coming_soon',
        'description': '规划中 - Messenger + 主页'
    },
    'messenger': {
        'name': 'Messenger',
        'icon': '💙',
        'color': '#006aff',
        'status': 'coming_soon',
        'description': '规划中 - 独立客户端'
    },
    'wechat': {
        'name': '微信 WeChat',
        'icon': '💚',
        'color': '#07c160',
        'status': 'coming_soon',
        'description': '规划中 - 个人号/公众号'
    },
    'instagram': {
        'name': 'Instagram',
        'icon': '📷',
        'color': '#E4405F',
        'status': 'coming_soon',
        'description': '规划中 - DM 自动回复'
    },
    'twitter': {
        'name': 'Twitter/X',
        'icon': '🐦',
        'color': '#1DA1F2',
        'status': 'coming_soon',
        'description': '规划中 - DM + 提及回复'
    },
    'discord': {
        'name': 'Discord',
        'icon': '💜',
        'color': '#5865F2',
        'status': 'coming_soon',
        'description': '规划中 - 服务器 Bot'
    }
}

TG_GROUP_CACHE_FILE = os.path.join("platforms", "telegram", "group_cache.json")
TG_SELECTED_GROUPS_FILE = os.path.join("platforms", "telegram", "selected_groups.json")
TG_LOG_DIR = os.path.join("platforms", "telegram", "logs")
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
    """加载平台配置"""
    config_file = f"platforms/{platform}/config.json"
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_platform_config(platform, config):
    """保存平台配置"""
    config_file = f"platforms/{platform}/config.json"
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def render_platform_selector():
    """渲染平台选择器（优化紧凑版）"""
    st.sidebar.markdown("### 🌐 平台")
    
    selected_platform = st.session_state.get('selected_platform', 'telegram')
    
    for platform_id, platform_info in PLATFORMS.items():
        # 创建紧凑的平台选项
        col1, col2, col3 = st.sidebar.columns([1, 3, 1])
        
        with col1:
            st.markdown(f"<div style='font-size: 1.5rem;'>{platform_info['icon']}</div>", 
                      unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<small>**{platform_info['name']}**</small>", 
                      unsafe_allow_html=True)
        
        with col3:
            # 状态标识（简化版）
            if platform_info['status'] == 'available':
                st.markdown("🟢", unsafe_allow_html=True)
            elif platform_info['status'] == 'coming_soon':
                st.markdown("🟡", unsafe_allow_html=True)
            else:
                st.markdown("🔴", unsafe_allow_html=True)
        
        # 选择按钮（紧凑版）
        button_label = "✓" if selected_platform == platform_id else "选择"
        if st.sidebar.button(
            button_label,
            key=f"select_{platform_id}",
            disabled=(platform_info['status'] != 'available'),
            use_container_width=True,
            type="primary" if selected_platform == platform_id else "secondary"
        ):
            st.session_state.selected_platform = platform_id
            st.rerun()
    
    return selected_platform

def render_telegram_panel():
    """渲染 Telegram 控制面板"""
    from admin import (
        get_bot_status, start_bot, stop_bot, 
        read_file, write_file, read_logs
    )
    
    st.header("📱 Telegram AI Bot 控制面板")
    
    # 状态显示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        is_running, pid = get_bot_status()
        if is_running:
            st.success(f"🟢 运行中 (PID: {pid})")
        else:
            st.error("🔴 已停止")
    
    with col2:
        if os.path.exists("userbot_session.session"):
            st.success("✅ 已登录")
        else:
            st.warning("⚠️ 未登录")
            if st.button("\u672a\u767b\u5f55 Telegram\uff08\u70b9\u51fb\u767b\u5f55\uff09", use_container_width=True, key="tg_login"):
                st.session_state.show_login_panel = True
    
    with col3:
        if os.path.exists(".env"):
            st.success("✅ 已配置")
        else:
            st.error("❌ 未配置")
    
    st.divider()

    if st.session_state.get("show_login_panel"):
        with st.expander("Telegram \u767b\u5f55", expanded=True):
            from admin import render_login_panel
            render_login_panel()


    
    # 控制按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 启动机器人", use_container_width=True, type="primary", 
                    disabled=is_running):
            success, message = start_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button("⛔ 停止机器人", use_container_width=True, 
                    disabled=not is_running):
            success, message = stop_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col3:
        if st.button("🔄 重启机器人", use_container_width=True,
                    disabled=not is_running):
            stop_bot()
            import time
            time.sleep(1)
            start_bot()
            st.success("机器人已重启")
            st.rerun()
    
    st.divider()
    
    # Tab 界面（使用 radio 避免按钮触发后回到默认页）
    panel_tabs = ["🧠 配置", "📢 群发", "📜 日志", "📊 统计"]
    active_tab = st.radio(
        "telegram_tabs",
        panel_tabs,
        horizontal=True,
        label_visibility="collapsed",
        key="tg_panel_tab"
    )

    if active_tab == panel_tabs[0]:
        render_telegram_config()
    elif active_tab == panel_tabs[1]:
        render_telegram_broadcast()
    elif active_tab == panel_tabs[2]:
        render_telegram_logs()
    else:
        render_telegram_stats()

def render_telegram_config():
    """Telegram 配置界面"""
    from admin import read_file, write_file
    
    st.subheader("⚙️ 配置管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**AI 人设**")
        prompt = st.text_area(
            "编辑提示词",
            value=read_file("prompt.txt"),
            height=200,
            key="tg_prompt"
        )
        if st.button("💾 保存人设", key="save_prompt"):
            write_file("prompt.txt", prompt)
            st.success("✅ 已保存")
    
    with col2:
        st.markdown("**触发关键词**")
        keywords = st.text_area(
            "每行一个",
            value=read_file("keywords.txt", "帮我\n求助\nAI"),
            height=200,
            key="tg_keywords"
        )
        if st.button("💾 保存关键词", key="save_keywords"):
            write_file("keywords.txt", keywords)
            st.success("✅ 已保存")
    
    st.divider()

    st.markdown("**QA问题库**")
    qa_path = os.path.join("platforms", "telegram", "qa.txt")
    qa_content = read_file(qa_path, "")
    qa_text = st.text_area(
        "QA问题库（支持 Q:/A: 或 question||answer）",
        value=qa_content,
        height=220,
        key="tg_qa_text"
    )
    if st.button("💾 保存QA", key="save_tg_qa"):
        success, message = write_file(qa_path, qa_text)
        if success:
            st.success("✅ 已保存")
        else:
            st.error(f"❌ {message}")

    st.divider()
    
    # 功能开关
    st.markdown("**功能开关**")
    config_content = read_file("platforms/telegram/config.txt", "PRIVATE_REPLY=on\nGROUP_REPLY=on")
    
    current_config = {'PRIVATE_REPLY': True, 'GROUP_REPLY': True}
    for line in config_content.split('\n'):
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().lower()
            if key in current_config:
                current_config[key] = (value == 'on')
    
    col1, col2 = st.columns(2)
    
    with col1:
        private_reply = st.toggle(
            "私聊自动回复",
            value=current_config['PRIVATE_REPLY'],
            key="tg_private"
        )
    
    with col2:
        group_reply = st.toggle(
            "群聊自动回复",
            value=current_config['GROUP_REPLY'],
            key="tg_group"
        )
    
    if st.button("💾 保存开关", use_container_width=True):
        new_config = f"PRIVATE_REPLY={'on' if private_reply else 'off'}\nGROUP_REPLY={'on' if group_reply else 'off'}"
        write_file("platforms/telegram/config.txt", new_config)
        st.success("✅ 已保存")

    st.divider()

    st.subheader("📌 群白名单")
    groups = load_tg_group_cache()
    if not groups:
        st.info("暂无群组缓存，请先运行机器人并产生群聊记录。")
        return

    selected_ids = load_tg_selected_group_ids()
    options = [format_group_label(item) for item in groups]
    label_to_id = {format_group_label(item): item["id"] for item in groups}
    default_labels = [label for label in options if label_to_id.get(label) in selected_ids]

    selected_labels = st.multiselect(
        "选择允许自动回复的群组",
        options,
        default=default_labels,
        key="tg_whitelist_select"
    )
    if st.button("💾 保存白名单", key="save_tg_whitelist", use_container_width=True):
        save_tg_selected_group_ids([label_to_id[label] for label in selected_labels])
        st.success("✅ 白名单已保存")

def render_telegram_broadcast():
    """Telegram 群发界面"""
    st.subheader("📢 群发")
    st.warning("⚠️ 频繁群发可能导致账号被限制，建议小批量测试。")

    groups = load_tg_group_cache()
    if not groups:
        st.info("暂无群组缓存，请先运行机器人并产生群聊记录。")
        return

    selected_ids = load_tg_selected_group_ids()
    mode = st.radio(
        "群组加载方式",
        ["白名单群组", "非白名单群组", "全部群组"],
        horizontal=True,
        key="tg_broadcast_mode"
    )

    if st.button("加载群组", key="tg_load_groups", use_container_width=True):
        if mode == "白名单群组":
            filtered = [g for g in groups if g["id"] in selected_ids]
        elif mode == "非白名单群组":
            filtered = [g for g in groups if g["id"] not in selected_ids]
        else:
            filtered = groups
        st.session_state.tg_broadcast_groups = filtered
        st.session_state.tg_broadcast_selected = [format_group_label(g) for g in filtered]
        st.rerun()

    loaded_groups = st.session_state.get("tg_broadcast_groups", [])
    if not loaded_groups:
        st.info("请先点击“加载群组”。")
        return

    options = [format_group_label(item) for item in loaded_groups]
    label_to_id = {format_group_label(item): item["id"] for item in loaded_groups}

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("全选", key="tg_select_all", use_container_width=True):
            st.session_state.tg_broadcast_selected = list(options)
            st.rerun()
    with col_b:
        if st.button("全不选", key="tg_select_none", use_container_width=True):
            st.session_state.tg_broadcast_selected = []
            st.rerun()
    with col_c:
        if st.button("反选", key="tg_select_invert", use_container_width=True):
            current = set(st.session_state.get("tg_broadcast_selected", []))
            st.session_state.tg_broadcast_selected = [x for x in options if x not in current]
            st.rerun()

    multiselect_kwargs = {"options": options, "key": "tg_broadcast_selected"}
    if "tg_broadcast_selected" not in st.session_state:
        multiselect_kwargs["default"] = st.session_state.get("tg_broadcast_selected", [])
    selected_labels = st.multiselect("选择群组", **multiselect_kwargs)
    selected_chat_ids = [label_to_id[label] for label in selected_labels]

    interval_seconds = st.number_input(
        "群发间隔（秒）",
        min_value=0.0,
        value=3.0,
        step=0.5,
        key="tg_broadcast_interval"
    )
    message = st.text_area(
        "群发内容",
        placeholder="输入要群发的消息...",
        height=160,
        key="tg_broadcast_message"
    )

    if st.button("🚀 开始群发", type="primary", use_container_width=True, key="tg_broadcast_send"):
        if not selected_chat_ids:
            st.error("请至少选择一个群组。")
        elif not message.strip():
            st.error("请输入群发内容。")
        else:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def update_progress(current, total, label):
                progress_bar.progress(current / total)
                status_text.text(f"[{current}/{total}] 发送到: {label}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                group_map = {item["id"]: (item["title"] or str(item["id"])) for item in loaded_groups}
                records, success, failed, err = loop.run_until_complete(
                    send_broadcast_ids_with_interval(
                        selected_chat_ids,
                        message,
                        interval_seconds,
                        group_map=group_map,
                        progress_callback=update_progress
                    )
                )
            finally:
                loop.close()

            if err:
                st.error(f"❌ 群发失败: {err}")
            else:
                st.success(f"✅ 群发完成！成功: {success}, 失败: {failed}")
                st.session_state.tg_broadcast_records = records

    st.subheader("📋 群发记录")
    records = st.session_state.get("tg_broadcast_records", [])
    if not records:
        st.info("暂无群发记录。")
    else:
        st.table(records)
        if st.button("清空记录", key="tg_clear_broadcast_records", use_container_width=True):
            st.session_state.tg_broadcast_records = []
            st.rerun()

def render_telegram_logs():
    """Telegram 日志界面"""
    st.subheader("📜 运行日志")
    st.caption("读取系统、私聊、群聊日志（日志中区分 QA_REPLY / AI_REPLY）")

    log_tab1, log_tab2, log_tab3 = st.tabs(["系统日志", "私聊日志", "群聊日志"])

    def render_log_tab(tab_label, file_path, key_prefix):
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("加载日志", use_container_width=True, key=f"{key_prefix}_load"):
                st.session_state[f"{key_prefix}_content"] = read_log_file(file_path)
        with col2:
            if st.button("刷新", use_container_width=True, key=f"{key_prefix}_refresh"):
                st.session_state[f"{key_prefix}_content"] = read_log_file(file_path)
        with col3:
            if st.button("清空日志", use_container_width=True, key=f"{key_prefix}_clear"):
                try:
                    os.makedirs(TG_LOG_DIR, exist_ok=True)
                    open(file_path, 'w').close()
                    st.session_state[f"{key_prefix}_content"] = ""
                    st.success("已清空")
                except Exception as exc:
                    st.error(f"清空失败: {exc}")

        logs = st.session_state.get(f"{key_prefix}_content", "")
        if not logs:
            st.info("点击“加载日志”查看内容。")
        st.text_area(tab_label, value=logs, height=360, disabled=True, key=f"{key_prefix}_text")

    with log_tab1:
        render_log_tab("系统日志", TG_SYSTEM_LOG_FILE, "tg_log_system")
    with log_tab2:
        render_log_tab("私聊日志", TG_PRIVATE_LOG_FILE, "tg_log_private")
    with log_tab3:
        render_log_tab("群聊日志", TG_GROUP_LOG_FILE, "tg_log_group")

def render_telegram_stats():
    """Telegram 统计界面"""
    st.subheader("📊 使用统计")
    
    # 读取统计数据
    try:
        import json
        from datetime import datetime
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
            last_active = datetime.fromisoformat(stats['last_active'])
            st.caption(f"最后活跃: {last_active.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 重置按钮
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
        
    except Exception as e:
        st.error(f"读取统计失败: {e}")
        st.info("💡 统计数据将在机器人运行后生成")

# ==================== WhatsApp 面板 ====================

def get_whatsapp_status():
    """获取 WhatsApp 机器人运行状态"""
    pid_file = "platforms/whatsapp/bot.pid"
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
    """启动 WhatsApp 机器人"""
    try:
        # 检查 Node.js
        import subprocess
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "❌ 未检测到 Node.js，请先安装"
        
        # 检查依赖
        if not os.path.exists("platforms/whatsapp/node_modules"):
            return False, "❌ 请先运行 install.bat/sh 安装依赖"
        
        # 启动机器人
        whatsapp_dir = "platforms/whatsapp"
        log_file = os.path.join(whatsapp_dir, "bot.log")
        pid_file = os.path.join(whatsapp_dir, "bot.pid")
        
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
        
        if sys.platform == 'win32':
            process = subprocess.Popen(
                ['node', 'bot.js'],
                cwd=whatsapp_dir,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            process = subprocess.Popen(
                ['node', 'bot.js'],
                cwd=whatsapp_dir,
                stdout=log_handle,
                stderr=subprocess.STDOUT
            )
        
        # 保存 PID
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        # 注意：不要关闭 log_handle，让进程继续使用
        
        return True, f"✅ WhatsApp 机器人已启动 (PID: {process.pid})"
    except Exception as e:
        return False, f"❌ 启动失败: {str(e)}"

def stop_whatsapp_bot():
    """停止 WhatsApp 机器人"""
    pid_file = "platforms/whatsapp/bot.pid"
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            import psutil
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
            
            os.remove(pid_file)
            return True, "✅ WhatsApp 机器人已停止"
        else:
            return False, "⚠️ 机器人未在运行"
    except Exception as e:
        return False, f"❌ 停止失败: {str(e)}"

def render_whatsapp_panel():
    """WhatsApp 主面板"""
    st.header("💬 WhatsApp 自动回复机器人")
    
    # 检查是否有二维码需要显示
    qr_image_path = "platforms/whatsapp/qr_code.png"
    status_file_path = "platforms/whatsapp/login_status.json"
    
    # 显示二维码弹窗
    if os.path.exists(qr_image_path) and os.path.exists(status_file_path):
        try:
            import json
            with open(status_file_path, 'r') as f:
                login_status = json.load(f)
            
            if login_status.get('status') == 'waiting' and login_status.get('qr_available'):
                with st.expander("📱 WhatsApp 登录二维码", expanded=True):
                    st.info("请使用手机 WhatsApp 扫描下方二维码登录")
                    st.image(qr_image_path, caption="扫描此二维码登录", width=400)
                    st.caption("提示：打开 WhatsApp > 设置 > 已连接的设备 > 连接设备")
                    st.caption("⏳ 二维码有效期约 20 秒，过期请重启机器人")
                    
                    if st.button("🔄 刷新查看状态", key="refresh_qr"):
                        st.rerun()
        except Exception as e:
            st.error(f"读取登录状态失败: {e}")
    
    # 状态显示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        is_running, pid = get_whatsapp_status()
        if is_running:
            st.success(f"🟢 运行中 (PID: {pid})")
        else:
            st.error("🔴 已停止")
    
    with col2:
        if os.path.exists("platforms/whatsapp/.wwebjs_auth"):
            st.success("✅ 已登录")
        else:
            st.warning("⚠️ 未登录")
    
    with col3:
        if os.path.exists(".env"):
            st.success("✅ 已配置")
        else:
            st.error("❌ 未配置")
    
    st.divider()
    
    # 控制按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 启动机器人", use_container_width=True, type="primary", 
                    disabled=is_running, key="whatsapp_start"):
            success, message = start_whatsapp_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button("⛔ 停止机器人", use_container_width=True, 
                    disabled=not is_running, key="whatsapp_stop"):
            success, message = stop_whatsapp_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col3:
        if st.button("🔄 重启机器人", use_container_width=True,
                    disabled=not is_running, key="whatsapp_restart"):
            stop_whatsapp_bot()
            import time
            time.sleep(1)
            start_whatsapp_bot()
            st.success("机器人已重启")
            st.rerun()
    
    st.divider()
    
    # Tab 界面
    tab1, tab2, tab3 = st.tabs([
        "🧠 配置", "📜 日志", "📊 统计"
    ])
    
    with tab1:
        render_whatsapp_config()
    
    with tab2:
        render_whatsapp_logs()
    
    with tab3:
        render_whatsapp_stats()

def render_whatsapp_config():
    """WhatsApp 配置界面"""
    from admin import read_file, write_file
    
    st.subheader("⚙️ 配置管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**AI 人设**")
        prompt = st.text_area(
            "编辑提示词",
            value=read_file("platforms/whatsapp/prompt.txt", "你是一个幽默的助手"),
            height=200,
            key="wa_prompt"
        )
        if st.button("💾 保存人设", key="wa_save_prompt"):
            write_file("platforms/whatsapp/prompt.txt", prompt)
            st.success("✅ 已保存")
    
    with col2:
        st.markdown("**触发关键词**")
        keywords = st.text_area(
            "群聊关键词（每行一个）",
            value=read_file("platforms/whatsapp/keywords.txt", "帮我\n求助\nAI"),
            height=200,
            key="wa_keywords"
        )
        if st.button("💾 保存关键词", key="wa_save_keywords"):
            write_file("platforms/whatsapp/keywords.txt", keywords)
            st.success("✅ 已保存")
    
    st.divider()
    
    st.markdown("**功能开关**")
    config_content = read_file("platforms/whatsapp/config.txt", "PRIVATE_REPLY=on\nGROUP_REPLY=on")
    
    col1, col2 = st.columns(2)
    
    with col1:
        private_reply = "on" if "PRIVATE_REPLY=on" in config_content else "off"
        private_enabled = st.toggle("私聊回复", value=(private_reply=="on"), key="wa_private")
    
    with col2:
        group_reply = "on" if "GROUP_REPLY=on" in config_content else "off"
        group_enabled = st.toggle("群聊回复", value=(group_reply=="on"), key="wa_group")
    
    if st.button("💾 保存开关配置", key="wa_save_config"):
        new_config = f"PRIVATE_REPLY={'on' if private_enabled else 'off'}\nGROUP_REPLY={'on' if group_enabled else 'off'}"
        write_file("platforms/whatsapp/config.txt", new_config)
        st.success("✅ 已保存")
    
    st.info("💡 修改后立即生效，无需重启机器人")

def render_whatsapp_logs():
    """WhatsApp 日志界面"""
    st.subheader("📜 运行日志")
    
    log_file = "platforms/whatsapp/bot.log"
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            last_modified = datetime.fromtimestamp(os.path.getmtime(log_file))
            st.caption(f"📁 文件大小: {file_size} 字节 | 📅 最后更新: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        if st.button("🔄 刷新日志", use_container_width=True, key="wa_refresh"):
            st.rerun()
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.read()
            
            if logs.strip():
                st.code(logs, language="log", line_numbers=False)
            else:
                st.info("📝 日志为空，等待机器人产生输出...")
        else:
            st.warning("⚠️ 日志文件不存在，请先启动机器人")
    except Exception as e:
        st.error(f"❌ 读取日志失败: {e}")
    
    if st.button("🗑️ 清空日志", key="wa_clear"):
        try:
            with open(log_file, 'w') as f:
                f.write("")
            st.success("✅ 日志已清空")
            st.rerun()
        except:
            st.error("❌ 清空失败")

def render_whatsapp_stats():
    """WhatsApp 统计界面"""
    st.subheader("📊 使用统计")
    
    # 读取统计数据
    try:
        import json
        from datetime import datetime
        with open("platforms/whatsapp/stats.json", 'r', encoding='utf-8') as f:
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
            last_active = datetime.fromisoformat(stats['last_active'])
            st.caption(f"最后活跃: {last_active.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 重置按钮
        if st.button("🗑️ 重置统计", use_container_width=True, key="wa_reset_stats"):
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
            st.success("✅ 统计已重置")
            st.rerun()
        
    except Exception as e:
        st.error(f"读取统计失败: {e}")
        st.info("💡 统计数据将在机器人运行后生成")

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

def main():
    if 'show_login_panel' not in st.session_state:
        st.session_state.show_login_panel = False

    """主函数"""
    # 标题
    st.markdown('<div class="main-header">👑鼎盛👑内部工具</div>', 
                unsafe_allow_html=True)
    
    # 初始化 session state
    if 'selected_platform' not in st.session_state:
        st.session_state.selected_platform = 'telegram'
    
    # 左侧平台选择器
    selected_platform = render_platform_selector()
    
    # 侧边栏底部信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 系统信息")
    st.sidebar.caption(f"Python: {sys.version.split()[0]}")
    st.sidebar.caption(f"Streamlit: {st.__version__}")
    
    # 右侧主面板
    platform_info = PLATFORMS[selected_platform]
    
    if platform_info['status'] == 'available':
        if selected_platform == 'telegram':
            render_telegram_panel()
        elif selected_platform == 'whatsapp':
            render_whatsapp_panel()
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
