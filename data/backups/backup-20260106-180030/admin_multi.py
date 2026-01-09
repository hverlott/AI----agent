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
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

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
        "platform_knowledge": "知识库",
        "platform_audit": "审核配置",
        "platform_telegram": "Telegram",
        "platform_whatsapp": "WhatsApp",
        "platform_accounts": "账号管理",
        "platform_ai_config": "AGNT AI配置中心",
        "platform_api_gateway": "API接口管理中心",
        "flow_tab": "时序图",
        "role": "身份切换",
        "tenant": "租户",
        "language": "语言"
    },
    "en": {
        "platform_knowledge": "Knowledge Base",
        "platform_audit": "Audit Config",
        "platform_telegram": "Telegram",
        "platform_whatsapp": "WhatsApp",
        "platform_accounts": "Accounts",
        "platform_ai_config": "AGNT AI Config",
        "platform_api_gateway": "API Gateway",
        "flow_tab": "Flow",
        "role": "Role",
        "tenant": "Tenant",
        "language": "Language"
    }
}
def tr(key):
    lang = st.session_state.get("lang", "zh")
    return I18N.get(lang, I18N["zh"]).get(key, key)

# 平台配置
PLATFORMS = {
    'knowledge': {
        'name': '📚',
        'icon': '📚',
        'color': '#8b5cf6',
        'status': 'available',
        'description': '知识库配置与检索',
        'roles': ['Admin', 'Auditor', 'Operator']
    },
    'audit': {
        'name': '🛡️',
        'icon': '🛡️',
        'color': '#FF5733',
        'status': 'available',
        'description': '关键词与日志管理',
        'roles': ['Auditor']
    },
    'telegram': {
        'name': 'Telegram',
        'icon': '📱',
        'color': '#0088cc',
        'status': 'available',  # available, unavailable, coming_soon
        'description': '全功能支持 - 私聊/群聊/频道',
        'roles': ['Admin', 'Auditor', 'Operator']
    },
    'whatsapp': {
        'name': 'WhatsApp',
        'icon': '💬',
        'color': '#25D366',
        'status': 'available',
        'description': '✅ 可用 - 私聊/群聊自动回复',
        'roles': ['Admin', 'Operator']
    },
    'accounts': {
        'name': '账号管理',
        'icon': '👥',
        'color': '#4b5563',
        'status': 'available',
        'description': '集中录入与分组/标签管理',
        'roles': ['Admin', 'TenantAdmin']
    },
    'ai_config': {
        'name': 'AGNT AI配置中心',
        'icon': '🧠',
        'color': '#0ea5e9',
        'status': 'available',
        'description': 'AI服务商接入与A/B测试',
        'roles': ['Admin']
    },
    'api_gateway': {
        'name': 'API接口管理中心',
        'icon': '🛣️',
        'color': '#16a34a',
        'status': 'available',
        'description': '统一网关/权限/流控/日志',
        'roles': ['Admin']
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
    
    # 角色过滤：非审核员隐藏“审核配置”平台入口
    current_role = st.session_state.get('user_role', 'Admin')
    for platform_id, platform_info in PLATFORMS.items():
        roles = platform_info.get('roles')
        if roles and current_role not in roles:
            continue
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
                pages.append(reader.pages[i].extract_text() or "")
            content = "\n".join(pages).strip()
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
    st.header("📚 知识库配置与管理")
    if st.session_state.get("kb_import_success"):
        st.success(st.session_state.get("kb_import_success"))
        del st.session_state["kb_import_success"]
    if st.session_state.get("kb_text_success"):
        st.success(st.session_state.get("kb_text_success"))
        del st.session_state["kb_text_success"]
    tabs = st.tabs(["管理", "导入", "检索测试", "设置"])

    with tabs[0]:
        st.subheader("知识条目列表")
        db = load_kb_db()
        items = db.get("items", [])
        if not items:
            st.info("暂无条目，可在“导入”或下方创建。")
        else:
            cols = st.columns([2, 2, 2, 2, 2])
            cols[0].markdown("**标题**")
            cols[1].markdown("**分类**")
            cols[2].markdown("**标签**")
            cols[3].markdown("**来源文件**")
            cols[4].markdown("**操作**")
            for idx, it in enumerate(items):
                t, c, tags, src = it.get("title",""), it.get("category",""), (it.get("tags") or []), it.get("source_file","")
                cols = st.columns([2,2,2,2,2])
                cols[0].write(t or "(未命名)")
                cols[1].write(c or "-")
                cols[2].write(", ".join(tags) if tags else "-")
                src_disp = os.path.basename(src) if src else "-"
                cols[3].write(src_disp)
                with cols[4]:
                    edit_key = f"kb_edit_{idx}"
                    del_key = f"kb_del_{idx}"
                    if st.button("编辑", key=edit_key):
                        st.session_state.kb_edit_index = idx
                    if st.button("删除", key=del_key):
                        db["items"].pop(idx)
                        save_kb_db(db)
                        st.success("已删除")
                        st.rerun()
        st.divider()
        st.subheader("新建文本条目")
        title = st.text_input("标题", key="kb_new_title")
        category = st.text_input("分类", key="kb_new_category")
        tags = st.text_input("标签（逗号分隔）", key="kb_new_tags")
        content = st.text_area("内容", height=180, key="kb_new_content")
        if st.button("保存条目", type="primary", key="kb_save_text"):
            if not title.strip() and not content.strip():
                st.error("请输入标题或内容")
            else:
                db = load_kb_db()
                item = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    "title": title.strip(),
                    "category": category.strip(),
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "content": content.strip(),
                    "source_file": "",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                db["items"].append(item)
                save_kb_db(db)
                st.session_state["kb_text_success"] = f"✅ 条目已保存：{item['title'] or '(未命名)'}。可在“管理”查看或在“检索测试”试用。"
                st.rerun()

        if "kb_edit_index" in st.session_state:
            idx = st.session_state.kb_edit_index
            db = load_kb_db()
            if 0 <= idx < len(db["items"]):
                st.divider()
                st.subheader("编辑条目")
                it = db["items"][idx]
                etitle = st.text_input("标题", value=it.get("title",""), key="kb_edit_title")
                ecategory = st.text_input("分类", value=it.get("category",""), key="kb_edit_category")
                etags = st.text_input("标签", value=",".join(it.get("tags") or []), key="kb_edit_tags")
                econtent = st.text_area("内容", value=it.get("content",""), height=180, key="kb_edit_content")
                if st.button("保存修改", type="primary", key="kb_edit_save"):
                    it["title"] = etitle.strip()
                    it["category"] = ecategory.strip()
                    it["tags"] = [t.strip() for t in etags.split(",") if t.strip()]
                    it["content"] = econtent.strip()
                    it["updated_at"] = datetime.now().isoformat()
                    save_kb_db(db)
                    st.success("✅ 已更新")
                    del st.session_state["kb_edit_index"]
                    st.rerun()
                if st.button("取消编辑", key="kb_edit_cancel"):
                    del st.session_state["kb_edit_index"]
                    st.rerun()

    with tabs[1]:
        st.subheader("导入文件")
        uploaded = st.file_uploader("选择文件（支持 txt/md/pdf/docx/xlsx）", type=["txt","md","pdf","docx","xlsx"], key="kb_file_uploader")
        if uploaded:
            safe_name = uploaded.name
            ensure_kb_dirs()
            dest_path = os.path.join(KB_FILES_DIR, safe_name)
            with open(dest_path, "wb") as f:
                f.write(uploaded.getvalue())
            content, note = extract_content_from_upload(uploaded, safe_name)
            st.info(f"解析状态: {note or 'ok'}")
            title = st.text_input("标题", value=os.path.splitext(safe_name)[0], key="kb_import_title")
            category = st.text_input("分类", key="kb_import_category")
            tags = st.text_input("标签（逗号分隔）", key="kb_import_tags")
            preview = st.text_area("内容预览（可编辑）", value=content, height=200, key="kb_import_preview")
            if st.button("保存为条目", type="primary", key="kb_import_save"):
                db = load_kb_db()
                item = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    "title": title.strip(),
                    "category": category.strip(),
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "content": preview.strip(),
                    "source_file": os.path.relpath(dest_path, BASE_DIR),
                    "parse_note": note,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                db["items"].append(item)
                save_kb_db(db)
                st.session_state["kb_import_success"] = f"✅ 已导入为知识条目：{item['title'] or safe_name}。可在“管理”查看或在“检索测试”试用。"
                st.rerun()

    with tabs[2]:
        st.subheader("检索测试")
        query = st.text_input("输入检索关键词或问题", key="kb_query")
        topn = st.number_input("返回条数", min_value=1, max_value=10, value=3, step=1, key="kb_topn")
        if st.button("执行检索", key="kb_search"):
            from main import retrieve_kb_context
            db = load_kb_db()
            items = db.get("items", [])
            import time
            t0 = time.time()
            ranked = retrieve_kb_context(query, items, topn=int(topn))
            elapsed_ms = (time.time() - t0) * 1000
            st.info(f"检索耗时: {elapsed_ms:.2f} ms，返回 {len(ranked)} 条")
            for it in ranked:
                st.write(f"- {it.get('title','(未命名)')}  | 分类: {it.get('category','-')} | 标签: {', '.join(it.get('tags') or [])}")
                st.caption(it.get("content","")[:300])

    with tabs[3]:
        st.subheader("设置与依赖")
        st.caption("用于文档解析的可选依赖：PyPDF2、python-docx、openpyxl。")
        missing = []
        try:
            import PyPDF2
        except Exception:
            missing.append("PyPDF2")
        try:
            import docx
        except Exception:
            missing.append("python-docx")
        try:
            import openpyxl
        except Exception:
            missing.append("openpyxl")
        if missing:
            st.warning("缺少依赖：" + ", ".join(missing))
        else:
            st.success("解析依赖已安装")

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
                    disabled=is_running, key="tg_start"):
            success, message = start_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button("⛔ 停止机器人", use_container_width=True, 
                    disabled=not is_running, key="tg_stop"):
            success, message = stop_bot()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col3:
        if st.button("🔄 重启机器人", use_container_width=True,
                    disabled=not is_running, key="tg_restart"):
            stop_bot()
            import time
            time.sleep(1)
            start_bot()
            st.success("机器人已重启")
            st.rerun()
    
    st.divider()
    
    # Tab 界面（使用 radio 避免按钮触发后回到默认页）
    panel_tabs = ["🧠 配置", "📢 群发", "📜 日志", "📊 统计", "🧭 时序图"]
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
    elif active_tab == panel_tabs[4]:
        render_telegram_flow()
    else:
        render_telegram_stats()

def render_telegram_config():
    """Telegram 配置界面"""
    from admin import read_file, write_file
    
    st.subheader("⚙️ 配置管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**AI 人设**")
        prompt_path = os.path.join("platforms", "telegram", "prompt.txt")
        prompt = st.text_area(
            "编辑提示词",
            value=read_file(prompt_path),
            height=200,
            key="tg_prompt"
        )
        if st.button("💾 保存人设", key="save_prompt"):
            write_file(prompt_path, prompt)
            st.success("✅ 已保存")
    
    with col2:
        st.markdown("**触发关键词**")
        keywords_path = os.path.join("platforms", "telegram", "keywords.txt")
        keywords = st.text_area(
            "每行一个",
            value=read_file(keywords_path, "帮我\n求助\nAI"),
            height=200,
            key="tg_keywords"
        )
        if st.button("💾 保存关键词", key="save_keywords"):
            write_file(keywords_path, keywords)
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
    
    # 功能开关与参数
    st.markdown("**功能开关**")
    config_content = read_file("platforms/telegram/config.txt", "PRIVATE_REPLY=on\nGROUP_REPLY=on")
    
    current_config = {
        'PRIVATE_REPLY': True, 
        'GROUP_REPLY': True, 
        'AI_TEMPERATURE': 0.7,
        'AUDIT_ENABLED': True,
        'AUDIT_MAX_RETRIES': 3,
        'AUDIT_TEMPERATURE': 0.0,
        'AUDIT_MODE': 'local',
        'AUDIT_SERVERS': 'http://127.0.0.1:8000',
        'AUTO_QUOTE': False,
        'QUOTE_INTERVAL_SECONDS': 30.0,
        'QUOTE_MAX_LEN': 200
    }
    for line in config_content.split('\n'):
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().lower()
            if key in ['PRIVATE_REPLY', 'GROUP_REPLY', 'AUDIT_ENABLED', 'AUTO_QUOTE']:
                current_config[key] = (value == 'on')
            elif key == 'AI_TEMPERATURE':
                try:
                    current_config[key] = float(value)
                except ValueError:
                    pass
            elif key == 'AUDIT_TEMPERATURE':
                try:
                    current_config[key] = float(value)
                except ValueError:
                    pass
            elif key == 'AUDIT_MAX_RETRIES':
                try:
                    current_config[key] = int(value)
                except ValueError:
                    pass
            elif key == 'AUDIT_MODE':
                current_config[key] = value
            elif key == 'AUDIT_SERVERS':
                current_config[key] = line.split('=', 1)[1].strip()
            elif key == 'QUOTE_INTERVAL_SECONDS':
                try:
                    current_config[key] = float(value)
                except ValueError:
                    pass
            elif key == 'QUOTE_MAX_LEN':
                try:
                    current_config[key] = int(value)
                except ValueError:
                    pass
    
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
    
    st.divider()
    st.markdown("**引用设置**")
    qcol1, qcol2, qcol3 = st.columns([1, 1, 1])
    with qcol1:
        auto_quote = st.toggle("自动引用", value=current_config['AUTO_QUOTE'], key="tg_auto_quote")
    with qcol2:
        quote_interval = st.number_input("引用时间间隔(秒)", min_value=5.0, max_value=120.0, value=float(current_config['QUOTE_INTERVAL_SECONDS']), step=5.0, key="tg_quote_interval")
    with qcol3:
        quote_max_len = st.number_input("引用内容长度(字符)", min_value=50, max_value=500, value=int(current_config['QUOTE_MAX_LEN']), step=10, key="tg_quote_max_len")
    
    st.divider()

    # AI 温度配置
    st.markdown("**🌡️ AI 创造性 (Temperature)**")
    
    temp_col1, temp_col2 = st.columns([2, 1])
    
    with temp_col1:
        ai_temperature = st.slider(
            "调整 AI 回复的随机性与创造性",
            min_value=0.0,
            max_value=1.0,
            value=current_config['AI_TEMPERATURE'],
            step=0.1,
            help="数值越大越有创造性，数值越小越保守精确",
            key="tg_temp_slider"
        )
        st.caption(f"当前设置值: **{ai_temperature:.1f}**")
    
    with temp_col2:
        st.info("""
        **参数说明：**
        - **0.0**: 最保守精确
        - **0.3**: 平衡准确性
        - **0.5**: 适度创造性
        - **0.7**: 较好创造性 (推荐)
        - **1.0**: 最大创造性
        """)
    
    st.divider()
    st.markdown("**🛡️ 内容审核系统 (双机拦截)**")
    
    audit_col1, audit_col2 = st.columns(2)
    with audit_col1:
        audit_enabled = st.toggle("启用审核员 AI", value=current_config['AUDIT_ENABLED'], key="tg_audit_enabled")
        
        # 审核模式选择
        mode_idx = 0 if current_config['AUDIT_MODE'] == 'local' else 1
        audit_mode = st.radio(
            "审核模式", 
            ["local", "remote"], 
            index=mode_idx, 
            key="tg_audit_mode", 
            horizontal=True,
            help="local: 本机运行; remote: 调用远程集群 (支持故障切换)"
        )
        
    with audit_col2:
        audit_max_retries = st.number_input("最大重试次数", min_value=1, max_value=5, value=current_config['AUDIT_MAX_RETRIES'], key="tg_audit_retries")
        audit_temperature = st.slider("审核员严格度", 0.0, 1.0, current_config['AUDIT_TEMPERATURE'], 0.1, key="tg_audit_temp")
        st.caption("建议设置：0.0 (最严格)")
        guide_strength = st.slider("合规引导强度", 0.0, 1.0, float(current_config.get('AUDIT_GUIDE_STRENGTH', 0.7)), 0.1, key="tg_audit_guide_strength")
        st.caption("数值越大，引导越严格（影响生成前的隐式合规提示）")

    col_tmp1, col_tmp2 = st.columns(2)
    with col_tmp1:
        if st.button("⏸️ 临时关闭审核（5分钟）", key="tg_audit_temp_off", use_container_width=True):
            st.session_state['audit_prev_enabled'] = audit_enabled
            import time as _time
            st.session_state['audit_temp_disable_until'] = _time.time() + 300
            saved = read_file("platforms/telegram/config.txt", "")
            lines = []
            for line in saved.splitlines():
                if line.strip().startswith("AUDIT_ENABLED="):
                    lines.append("AUDIT_ENABLED=off")
                else:
                    lines.append(line)
            write_file("platforms/telegram/config.txt", "\n".join(lines))
            st.success("✅ 审核已临时关闭，5分钟后自动恢复")
    with col_tmp2:
        if st.button("▶️ 立即恢复审核配置", key="tg_audit_restore", use_container_width=True):
            prev = st.session_state.get('audit_prev_enabled', True)
            saved = read_file("platforms/telegram/config.txt", "")
            lines = []
            for line in saved.splitlines():
                if line.strip().startswith("AUDIT_ENABLED="):
                    lines.append(f"AUDIT_ENABLED={'on' if prev else 'off'}")
                else:
                    lines.append(line)
            write_file("platforms/telegram/config.txt", "\n".join(lines))
            st.success("✅ 审核配置已恢复")
    try:
        import time as _time
        until = st.session_state.get('audit_temp_disable_until')
        if until and _time.time() > until:
            prev = st.session_state.get('audit_prev_enabled', True)
            saved = read_file("platforms/telegram/config.txt", "")
            lines = []
            for line in saved.splitlines():
                if line.strip().startswith("AUDIT_ENABLED="):
                    lines.append(f"AUDIT_ENABLED={'on' if prev else 'off'}")
                else:
                    lines.append(line)
            write_file("platforms/telegram/config.txt", "\n".join(lines))
            st.session_state['audit_temp_disable_until'] = None
            st.success("✅ 审核已自动恢复")
    except Exception:
        pass
    # 远程服务器配置 (仅在 remote 模式下显示或生效)
    audit_servers = current_config['AUDIT_SERVERS']
    if audit_mode == 'remote':
        audit_servers = st.text_input(
            "远程审核服务器地址 (多个用逗号分隔)", 
            value=current_config['AUDIT_SERVERS'], 
            key="tg_audit_servers",
            help="例如: http://192.168.1.10:8000, http://192.168.1.11:8000"
        )

    if st.button("💾 保存配置", use_container_width=True):
        new_config = f"""# ========================================
# Telegram AI Bot - 功能配置
# ========================================

# 个人消息回复开关
PRIVATE_REPLY={'on' if private_reply else 'off'}

# 群消息回复开关
GROUP_REPLY={'on' if group_reply else 'off'}

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
        write_file("platforms/telegram/config.txt", new_config)
        st.success("✅ 配置已保存")

    st.markdown("**🔒 审核员关键词配置（双机拦截）**")
    from keyword_manager import KeywordManager
    km = KeywordManager()
    role_kw = st.session_state.get('user_role', 'Admin')
    can_edit_kw = (role_kw == 'Auditor')
    kwc1, kwc2 = st.columns(2)
    with kwc1:
        st.markdown("违禁词")
        blk = km.get_keywords().get('block', [])
        st.write(f"当前 {len(blk)} 项")
        if can_edit_kw:
            new_blk = st.text_input("添加违禁词", key="tg_kw_add_block")
            if st.button("添加", key="tg_kw_add_block_btn"):
                if new_blk:
                    ok, msg = km.add_keyword('block', new_blk)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            if blk:
                del_blk = st.selectbox("删除违禁词", [""] + blk, key="tg_kw_del_block")
                if st.button("删除选中", key="tg_kw_del_block_btn"):
                    if del_blk:
                        km.remove_keyword('block', del_blk)
                        st.success(f"已删除 {del_blk}")
                        st.rerun()
                rn_blk_col1, rn_blk_col2 = st.columns([1,1])
                with rn_blk_col1:
                    rn_blk_sel = st.selectbox("重命名目标", [""] + blk, key="tg_kw_rename_block_sel")
                with rn_blk_col2:
                    rn_blk_new = st.text_input("新名称", key="tg_kw_rename_block_new")
                if st.button("重命名", key="tg_kw_rename_block_btn"):
                    if rn_blk_sel and rn_blk_new:
                        ok, msg = km.rename_keyword('block', rn_blk_sel, rn_blk_new)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
        else:
            st.info("仅审核员可编辑")
        st.markdown(" ".join([f"`{k}`" for k in blk]))
    with kwc2:
        st.markdown("敏感词")
        sen = km.get_keywords().get('sensitive', [])
        st.write(f"当前 {len(sen)} 项")
        if can_edit_kw:
            new_sen = st.text_input("添加敏感词", key="tg_kw_add_sens")
            if st.button("添加", key="tg_kw_add_sens_btn"):
                if new_sen:
                    ok, msg = km.add_keyword('sensitive', new_sen)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            if sen:
                del_sen = st.selectbox("删除敏感词", [""] + sen, key="tg_kw_del_sens")
                if st.button("删除选中", key="tg_kw_del_sens_btn"):
                    if del_sen:
                        km.remove_keyword('sensitive', del_sen)
                        st.success(f"已删除 {del_sen}")
                        st.rerun()
                rn_sen_col1, rn_sen_col2 = st.columns([1,1])
                with rn_sen_col1:
                    rn_sen_sel = st.selectbox("重命名目标", [""] + sen, key="tg_kw_rename_sens_sel")
                with rn_sen_col2:
                    rn_sen_new = st.text_input("新名称", key="tg_kw_rename_sens_new")
                if st.button("重命名", key="tg_kw_rename_sens_btn"):
                    if rn_sen_sel and rn_sen_new:
                        ok, msg = km.rename_keyword('sensitive', rn_sen_sel, rn_sen_new)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
        else:
            st.info("仅审核员可编辑")
        st.markdown(" ".join([f"`{k}`" for k in sen]))
    st.divider()
    st.markdown("允许词（品牌设定白名单）")
    alw = km.get_keywords().get('allow', [])
    st.write(f"当前 {len(alw)} 项")
    if can_edit_kw:
        new_alw = st.text_input("添加允许词", key="tg_kw_add_allow")
        if st.button("添加", key="tg_kw_add_allow_btn"):
            if new_alw:
                ok, msg = km.add_keyword('allow', new_alw)
                if ok: st.success(msg)
                else: st.warning(msg)
                st.rerun()
        if alw:
            del_alw = st.selectbox("删除允许词", [""] + alw, key="tg_kw_del_allow")
            if st.button("删除选中", key="tg_kw_del_allow_btn"):
                if del_alw:
                    km.remove_keyword('allow', del_alw)
                    st.success(f"已删除 {del_alw}")
                    st.rerun()
            rn_alw_col1, rn_alw_col2 = st.columns([1,1])
            with rn_alw_col1:
                rn_alw_sel = st.selectbox("重命名目标", [""] + alw, key="tg_kw_rename_allow_sel")
            with rn_alw_col2:
                rn_alw_new = st.text_input("新名称", key="tg_kw_rename_allow_new")
            if st.button("重命名", key="tg_kw_rename_allow_btn"):
                if rn_alw_sel and rn_alw_new:
                    ok, msg = km.rename_keyword('allow', rn_alw_sel, rn_alw_new)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
    else:
        st.info("仅审核员可编辑")
    st.markdown(" ".join([f"`{k}`" for k in alw]))

    st.markdown("**📝 审核员兜底话术库（每行一条）**")
    fallback_path = os.path.join("platforms", "telegram", "audit_fallback.txt")
    fallback_default = "您的问题已升级至特级顾问处理（前白宫总统顾问团成员）\n正在为您连接专属服务通道，请稍候\n系统正在为您分配VIP服务专员"
    fallback_text = st.text_area(
        "编辑兜底话术",
        value=read_file(fallback_path, fallback_default),
        height=160,
        key="tg_audit_fallback"
    )
    if st.button("💾 保存兜底话术", key="save_audit_fallback", use_container_width=True):
        write_file(fallback_path, fallback_text)
        st.success("✅ 已保存")

    st.markdown("**🧹 QA 知识库清理**")
    qa_path = os.path.join("platforms", "telegram", "qa.txt")
    if st.button("🔎 扫描并清理不合规条目", key="tg_qa_clean", use_container_width=True):
        raw = read_file(qa_path, "")
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
        write_file(qa_path, "\n".join(cleaned))
        st.success(f"✅ 清理完成，移除 {removed} 条不合规条目")

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

    log_tab1, log_tab2, log_tab3, log_tab4 = st.tabs(["系统日志", "私聊日志", "群聊日志", "审核日志"])

    def render_log_tab(tab_label, file_path, key_prefix):
        if f"{key_prefix}_content" not in st.session_state:
            st.session_state[f"{key_prefix}_content"] = read_log_file(file_path)
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
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
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
    with log_tab4:
        render_log_tab("审核日志", os.path.join("platforms", "telegram", "logs", "audit.log"), "tg_log_audit")

def render_telegram_flow():
    st.subheader("🧭 客户到 AI 回复时序")
    st.markdown("**入口**：用户在 Telegram 发送消息 → Telethon 捕获 NewMessage → main.py 统一处理")
    st.markdown("**触发检查**：私聊/被@/关键词/上下文/群白名单")
    st.markdown("---")
    st.markdown("**分支 A：QA 命中**")
    st.markdown("- 解析 qa.txt 匹配固定答案")
    st.markdown("- 直接回复到 Telegram")
    st.markdown("- 写入日志与更新统计")
    st.markdown("---")
    st.markdown("**分支 B：QA 未命中**")
    st.markdown("- 检索知识库 Top-2 作为上下文")
    st.markdown("- 调用 AI 生成草稿")
    st.markdown("- 关键词前置拦截：允许词优先；命中违禁/敏感→兜底")
    st.markdown("- 审核员 AI（双机拦截）：本地/远程，返回 PASS/FAIL 与建议")
    st.markdown("- FAIL 重试至上限，超限兜底；PASS 发送 AI 回复")
    st.markdown("- 写入审核与系统日志，更新统计")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**关键词优先级**")
        st.markdown("- allow：命中直接允许")
        st.markdown("- block：命中直接拒绝，触发兜底")
        st.markdown("- sensitive：记录并拒绝（可调整为警告）")
    with col2:
        st.markdown("**兜底话术**")
        st.markdown("- 来源：platforms/telegram/audit_fallback.txt")
        st.markdown("- 可在配置页直接编辑并保存")
    st.markdown("---")
    st.markdown("**文件与模块**")
    st.markdown("- 处理主链路：[main.py](file:///d:/AI%20Talk/main.py)")
    st.markdown("- 审核与兜底：[audit_manager.py](file:///d:/AI%20Talk/audit_manager.py)")
    st.markdown("- 关键词管理：[keyword_manager.py](file:///d:/AI%20Talk/keyword_manager.py)")
    st.markdown("- 配置后台：[admin_multi.py](file:///d:/AI%20Talk/admin_multi.py)")

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
    except Exception:
        pass

def render_accounts_panel():
    st.header("👥 账号管理")
    base = _ensure_data_dirs()
    tenant = st.session_state.get("tenant", "default")
    tdir = os.path.join(base, "tenants", tenant)
    os.makedirs(tdir, exist_ok=True)
    db_path = os.path.join(tdir, "accounts.json")
    try:
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
        else:
            db = {"accounts": []}
    except Exception:
        db = {"accounts": []}
    st.caption(f"当前租户: {tenant}")
    st.markdown("平台/账号集中录入与分组、标签管理")
    col1, col2 = st.columns(2)
    with col1:
        platform = st.selectbox("平台", ["WeChat", "Weibo", "Twitter", "Telegram", "WhatsApp"], key="acc_platform")
        username = st.text_input("账号名/ID", key="acc_username")
        group = st.text_input("分组", key="acc_group")
    with col2:
        tags = st.text_input("标签（逗号分隔）", key="acc_tags")
        refresh = st.number_input("刷新间隔（分钟）", min_value=5, max_value=1440, value=60, step=5, key="acc_refresh")
    if st.button("添加/更新账号", use_container_width=True, key="acc_add"):
        item = {"platform": platform, "username": username, "group": group, "tags": [t.strip() for t in tags.split(",") if t.strip()], "refresh_minutes": int(refresh), "updated_at": datetime.now().isoformat()}
        found = False
        for i, a in enumerate(db["accounts"]):
            if a["platform"] == platform and a["username"] == username:
                db["accounts"][i] = item
                found = True
                break
        if not found:
            db["accounts"].append(item)
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        log_admin_op("accounts_upsert", {"platform": platform, "username": username})
        st.success("✅ 已保存账号")
        st.rerun()
    st.divider()
    st.markdown("账号列表")
    st.table(db["accounts"])

def render_ai_config_panel():
    st.header("🧠 AGNT AI配置中心")
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
    st.caption(f"当前租户: {tenant}")
    st.markdown("可视化配置AI服务商、模型版本与A/B权重")
    col1, col2, col3 = st.columns(3)
    with col1:
        provider = st.selectbox("服务商", ["DeepSeek", "OpenAI", "AzureOpenAI", "LocalAI"], key="ai_provider")
        base_url = st.text_input("Base URL", key="ai_base_url")
    with col2:
        model = st.text_input("模型版本", key="ai_model")
        weight = st.slider("A/B权重", 0, 100, 50, key="ai_weight")
    with col3:
        api_key = st.text_input("API Key（不落盘展示）", type="password", key="ai_api_key")
        timeout = st.number_input("请求超时（秒）", min_value=1, max_value=60, value=10, step=1, key="ai_timeout")
    if st.button("保存配置", use_container_width=True, key="ai_save_cfg"):
        item = {"provider": provider, "base_url": base_url, "model": model, "weight": int(weight), "timeout": int(timeout), "updated_at": datetime.now().isoformat()}
        found = False
        for i, p in enumerate(cfg["providers"]):
            if p["provider"] == provider and p.get("model") == model:
                cfg["providers"][i] = item
                found = True
                break
        if not found:
            cfg["providers"].append(item)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        log_admin_op("ai_provider_upsert", {"provider": provider, "model": model, "api_key": api_key})
        st.success("✅ 已保存")
        st.rerun()
    st.divider()
    st.markdown("已配置列表")
    st.table(cfg["providers"])
    st.info("提示：API Key 不保存在列表中；仅用于运行时加载，请考虑环境变量或安全存储。")

def render_api_gateway_panel():
    st.header("🛣️ API接口管理中心")
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
        route = st.text_input("接口路径 /audit /reply", key="gw_route")
    with col2:
        method = st.selectbox("方法", ["GET","POST","PUT","DELETE"], key="gw_method")
    with col3:
        auth = st.selectbox("鉴权", ["None","Token","HMAC"], key="gw_auth")
    with col4:
        rate = st.number_input("流量限制 req/min", min_value=0, max_value=10000, value=60, step=10, key="gw_rate")
    if st.button("添加/更新路由", use_container_width=True, key="gw_add"):
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
        st.success("✅ 已保存路由")
        st.rerun()
    st.divider()
    st.markdown("路由列表")
    st.table(gw["routes"])

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
            last_active = datetime.fromisoformat(stats['last_active'])
            st.caption(f"最后活跃: {last_active.strftime('%Y-%m-%d %H:%M:%S')}")
        
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
    
    log_file = os.path.join(BASE_DIR, "platforms", "whatsapp", "bot.log")
    
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

def render_audit_panel():
    from keyword_manager import KeywordManager
    st.header("🛡️ 审核员配置中心")
    
    # 权限校验：仅审核员可访问
    role = st.session_state.get('user_role', 'Admin')
    if role != 'Auditor':
        st.warning("仅审核员可访问此模块。请在左侧切换身份为 Auditor。")
        return
    
    # Init manager
    km = KeywordManager()
    
    tab1, tab2 = st.tabs(["关键词管理", "审核日志"])
    
    with tab1:
        st.subheader("关键词配置")
        st.info("此处配置的关键词将实时生效，用于拦截或标记敏感内容。")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🚫 违禁词 (Block)")
            st.caption("触发此类关键词将直接拦截回复")
            keywords = km.get_keywords().get('block', [])
            
            # Display stats
            st.write(f"当前共 {len(keywords)} 个违禁词")
            
            # Add new
            new_block = st.text_input("添加违禁词", key="new_block_input")
            if st.button("添加", key="add_block_btn"):
                if new_block:
                    success, msg = km.add_keyword('block', new_block)
                    if success: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            
            # Remove
            if keywords:
                to_remove = st.selectbox("选择要删除的违禁词", [""] + keywords, key="del_block_sel")
                if st.button("删除选中", key="del_block_btn"):
                    if to_remove:
                        km.remove_keyword('block', to_remove)
                        st.success(f"已删除 {to_remove}")
                        st.rerun()
            
            # Rename
            if keywords:
                col_rename_b1, col_rename_b2 = st.columns([1, 1])
                with col_rename_b1:
                    to_rename = st.selectbox("选择重命名的违禁词", [""] + keywords, key="rename_block_sel")
                with col_rename_b2:
                    new_name = st.text_input("新的名称", key="rename_block_new")
                if st.button("重命名", key="rename_block_btn"):
                    if to_rename and new_name:
                        ok, msg = km.rename_keyword('block', to_rename, new_name)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
            
            # List all (Tag style)
            st.markdown("---")
            st.markdown(" ".join([f"`{k}`" for k in keywords]))

        with col2:
            st.markdown("#### ⚠️ 敏感词 (Sensitive)")
            st.caption("触发此类关键词将记录日志并拒绝（或警告）")
            keywords = km.get_keywords().get('sensitive', [])
            
            st.write(f"当前共 {len(keywords)} 个敏感词")
            
            new_sens = st.text_input("添加敏感词", key="new_sens_input")
            if st.button("添加", key="add_sens_btn"):
                if new_sens:
                    success, msg = km.add_keyword('sensitive', new_sens)
                    if success: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
            
            if keywords:
                to_remove_sens = st.selectbox("选择要删除的敏感词", [""] + keywords, key="del_sens_sel")
                if st.button("删除选中", key="del_sens_btn"):
                    if to_remove_sens:
                        km.remove_keyword('sensitive', to_remove_sens)
                        st.success(f"已删除 {to_remove_sens}")
                        st.rerun()
            
            # Rename
            if keywords:
                col_rename_s1, col_rename_s2 = st.columns([1, 1])
                with col_rename_s1:
                    to_rename_s = st.selectbox("选择重命名的敏感词", [""] + keywords, key="rename_sens_sel")
                with col_rename_s2:
                    new_name_s = st.text_input("新的名称", key="rename_sens_new")
                if st.button("重命名", key="rename_sens_btn"):
                    if to_rename_s and new_name_s:
                        ok, msg = km.rename_keyword('sensitive', to_rename_s, new_name_s)
                        if ok: st.success(msg)
                        else: st.warning(msg)
                        st.rerun()
            
            st.markdown("---")
            st.markdown(" ".join([f"`{k}`" for k in keywords]))

        st.divider()
        st.markdown("#### ✅ 允许词（品牌设定白名单）")
        allow_list = km.get_keywords().get('allow', [])
        st.write(f"当前共 {len(allow_list)} 个允许词")
        new_allow = st.text_input("添加允许词", key="new_allow_input")
        if st.button("添加", key="add_allow_btn"):
            if new_allow:
                success, msg = km.add_keyword('allow', new_allow)
                if success: st.success(msg)
                else: st.warning(msg)
                st.rerun()
        if allow_list:
            to_remove_allow = st.selectbox("选择要删除的允许词", [""] + allow_list, key="del_allow_sel")
            if st.button("删除选中", key="del_allow_btn"):
                if to_remove_allow:
                    km.remove_keyword('allow', to_remove_allow)
                    st.success(f"已删除 {to_remove_allow}")
                    st.rerun()
            col_rename_a1, col_rename_a2 = st.columns([1, 1])
            with col_rename_a1:
                to_rename_allow = st.selectbox("选择重命名的允许词", [""] + allow_list, key="rename_allow_sel")
            with col_rename_a2:
                new_name_allow = st.text_input("新的名称", key="rename_allow_new")
            if st.button("重命名", key="rename_allow_btn"):
                if to_rename_allow and new_name_allow:
                    ok, msg = km.rename_keyword('allow', to_rename_allow, new_name_allow)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun()
        st.markdown("---")
        st.markdown(" ".join([f"`{k}`" for k in allow_list]))

    with tab2:
        st.subheader("最近审核日志")
        log_file = os.path.join("platforms", "telegram", "logs", "audit.log")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("刷新日志", key="audit_log_refresh"):
                st.rerun()
            
        logs = read_log_file(log_file, 50)
        st.code(logs, language="text")

def main():
    if 'show_login_panel' not in st.session_state:
        st.session_state.show_login_panel = False

    """主函数"""
    # 标题
    st.markdown('<div class="main-header">👑鼎盛👑内部工具</div>', 
                unsafe_allow_html=True)
    
    # --- Role Selection ---
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'Admin' 
    if 'lang' not in st.session_state:
        st.session_state.lang = 'zh'
    if 'tenant' not in st.session_state:
        st.session_state.tenant = 'default'

    st.sidebar.markdown("### 👤 身份切换")
    role = st.sidebar.selectbox("当前角色", ["Admin", "Auditor", "Operator", "TenantAdmin"], key="role_selector")
    st.session_state.user_role = role
    st.sidebar.divider()
    st.sidebar.markdown("### 🌐 语言")
    lang_disp = st.sidebar.selectbox("语言", [LANGS["zh"], LANGS["en"]], key="lang_selector")
    st.session_state.lang = "zh" if lang_disp == LANGS["zh"] else "en"
    st.sidebar.markdown("### 🏷️ 租户")
    st.session_state.tenant = st.sidebar.text_input("租户ID", value=st.session_state.tenant, key="tenant_input")
    
    if role == 'Auditor':
        render_audit_panel()
        return
    # ----------------------
    
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
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🆘 帮助")
    try:
        st.sidebar.link_button("系统架构文档", "file:///d:/AI%20Talk/docs/System-Architecture.md", use_container_width=True)
        st.sidebar.link_button("知识库用户手册", "file:///d:/AI%20Talk/docs/KB-User-Guide.md", use_container_width=True)
    except Exception:
        st.sidebar.markdown("[系统架构文档](file:///d:/AI%20Talk/docs/System-Architecture.md)")
        st.sidebar.markdown("[知识库用户手册](file:///d:/AI%20Talk/docs/KB-User-Guide.md)")
    
    # 右侧主面板
    platform_info = PLATFORMS[selected_platform]
    
    if platform_info['status'] == 'available':
        if selected_platform == 'knowledge':
            render_kb_panel()
        elif selected_platform == 'audit':
            render_audit_panel()
        elif selected_platform == 'accounts':
            render_accounts_panel()
        elif selected_platform == 'ai_config':
            render_ai_config_panel()
        elif selected_platform == 'api_gateway':
            render_api_gateway_panel()
        elif selected_platform == 'telegram':
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
