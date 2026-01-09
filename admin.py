#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram AI Bot - Web 管理后台
基于 Streamlit 构建的图形化控制面板
"""

import streamlit as st
import os
import sys
import time
import random
import asyncio
import subprocess
import signal
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import json
import shutil
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

# 页面配置
st.set_page_config(
    page_title="Telegram AI 中控台",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 样式优化
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
            radial-gradient(1200px 500px at 10% -10%, #fff1d9 0%, transparent 60%),
            radial-gradient(1000px 600px at 95% 0%, #e3f0ff 0%, transparent 55%),
            var(--bg);
        color: var(--text);
        font-family: "Segoe UI", "Microsoft YaHei", "Noto Sans SC", sans-serif;
    }
    [data-testid="stSidebar"] {
        background: #fbfaf7;
        border-right: 1px solid var(--border);
    }
    .block-container {
        padding-top: 1.4rem;
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
    .status-running {
        color: #0f7a32;
        font-weight: 600;
    }
    .status-stopped {
        color: #b42318;
        font-weight: 600;
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
    .stTextArea textarea {
        border-radius: 12px;
        border: 1px solid var(--border);
        background: #ffffff;
    }
    .stTextArea textarea:focus {
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
    .stTextInput input {
        border-radius: 12px;
        border: 1px solid var(--border);
        background: #ffffff;
    }
    .stTextInput input:focus {
        border-color: rgba(15, 107, 109, 0.45);
        box-shadow: 0 0 0 3px rgba(15, 107, 109, 0.15);
    }
    details > summary {
        border-radius: 12px;
        background: #f8f5ef;
        border: 1px solid var(--border);
        padding: 0.4rem 0.8rem;
    }
    .block-container {
        max-width: 1200px;
    }
    .hint-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
    }
</style>
""", unsafe_allow_html=True)

# 全局变量
APP_VERSION = "V2.2"
BOT_PID_FILE = os.path.join(BASE_DIR, "bot.pid")
BOT_LOG_FILE = os.path.join(BASE_DIR, "bot.log")
LOG_DIR = os.path.join(BASE_DIR, "platforms", "telegram", "logs")
LOG_ARCHIVE_DIR = os.path.join(LOG_DIR, "archive")
SYSTEM_LOG_FILE = os.path.join(LOG_DIR, "system.log")
PRIVATE_LOG_FILE = os.path.join(LOG_DIR, "private.log")
GROUP_LOG_FILE = os.path.join(LOG_DIR, "group.log")

# ---- Log archive helpers ----
def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def archive_log_file(file_path, archive_dir, prefix):
    try:
        if (not os.path.exists(file_path)) or os.path.getsize(file_path) == 0:
            return None
        _ensure_dir(archive_dir)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.log"
        dest = os.path.join(archive_dir, filename)
        shutil.copy2(file_path, dest)
        return dest
    except Exception:
        return None

def archive_and_clear_log(file_path, archive_dir, prefix):
    archived = archive_log_file(file_path, archive_dir, prefix)
    try:
        _ensure_dir(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass
    return archived

def list_archive_files(archive_dir, prefix=None):
    if not os.path.exists(archive_dir):
        return []
    files = []
    for name in os.listdir(archive_dir):
        if prefix and (not name.startswith(prefix + "_")):
            continue
        path = os.path.join(archive_dir, name)
        if os.path.isfile(path):
            files.append(path)
    files.sort(reverse=True)
    return files

def read_raw_log_file(file_path):
    try:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def diagnose_env():
    missing = []
    invalid = []
    api_id = (os.getenv("TELEGRAM_API_ID") or "").strip()
    api_hash = (os.getenv("TELEGRAM_API_HASH") or "").strip()
    if not api_id:
        missing.append("TELEGRAM_API_ID")
    elif not api_id.isdigit():
        invalid.append("TELEGRAM_API_ID")
    if not api_hash:
        missing.append("TELEGRAM_API_HASH")

    ai_key = (os.getenv("AI_API_KEY") or "").strip()
    ai_base = (os.getenv("AI_BASE_URL") or "").strip()
    ai_model = (os.getenv("AI_MODEL_NAME") or "").strip()
    if not ai_key:
        missing.append("AI_API_KEY")
    if not ai_base:
        missing.append("AI_BASE_URL")
    if not ai_model:
        missing.append("AI_MODEL_NAME")

    return missing, invalid

# ==================== 工具函数 ====================

def get_bot_status(tenant_id=None):
    """检查机器人运行状态（支持租户隔离）"""
    if tenant_id:
        # 如果指定了租户，检查该租户的专属 PID 文件
        pid_file = f"data/tenants/{tenant_id}/platforms/telegram/bot.pid"
    else:
        # 兼容旧逻辑或默认情况（但不建议使用，应始终传 tenant_id）
        pid_file = BOT_PID_FILE

    if not os.path.exists(pid_file):
        return False, None
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        if sys.platform == 'win32':
            import psutil
            return psutil.pid_exists(pid), pid
        else:
            os.kill(pid, 0)
            return True, pid
    except (ValueError, ProcessLookupError, OSError):
        return False, None


def start_bot(tenant_id=None, session_name=None):
    """启动机器人（支持租户隔离）"""
    if not tenant_id:
        return False, "启动失败: 未指定租户 ID"

    is_running, _ = get_bot_status(tenant_id)
    if is_running:
        return False, "该租户的机器人已在运行中"
    
    # 租户隔离路径
    tenant_dir = f"data/tenants/{tenant_id}/platforms/telegram"
    os.makedirs(tenant_dir, exist_ok=True)
    
    pid_file = os.path.join(tenant_dir, "bot.pid")
    log_file_path = os.path.join(tenant_dir, "bot.log")

    try:
        env = os.environ.copy()
        env['TENANT_ID'] = tenant_id # 注入租户 ID
        
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            # 如果未指定 session_name，则尝试自动查找
            if not session_name:
                import json
                acc_db_path = f"data/tenants/{tenant_id}/accounts.json"
                session_name = "userbot_session"
                if os.path.exists(acc_db_path):
                    try:
                        with open(acc_db_path, "r", encoding="utf-8") as f:
                            acc_db = json.load(f)
                        # 查找 Telegram 平台且有 session_file 的第一个账号
                        for acc in acc_db.get("accounts", []):
                            if acc.get("platform") == "Telegram" and acc.get("session_file"):
                                # 去掉 .session 后缀
                                s_file = acc.get("session_file")
                                if s_file.endswith(".session"):
                                    session_name = s_file[:-8]
                                else:
                                    session_name = s_file
                                break
                    except:
                        pass
            
            # 确保 session_name 不带后缀
            if session_name.endswith(".session"):
                session_name = session_name[:-8]

            cmd = ['python', '-u', 'main.py', '--tenant', tenant_id, '--session', session_name]
            
            if sys.platform == 'win32':
                process = subprocess.Popen(
                    cmd,
                    env=env, # 注入环境变量
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    bufsize=1,  # 行缓冲
                    universal_newlines=True
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    env=env, # 注入环境变量
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setpgrp,
                    bufsize=1,  # 行缓冲
                    universal_newlines=True
                )
        
        # 保存 PID 到租户目录
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        # 等待一小段时间，确保进程启动
        time.sleep(0.5)
        
        return True, f"机器人已启动 (PID: {process.pid})"
    except Exception as e:
        return False, f"启动失败: {e}"


def stop_bot(tenant_id=None):
    """停止机器人（支持租户隔离）"""
    if not tenant_id:
        return False, "停止失败: 未指定租户 ID"

    is_running, pid = get_bot_status(tenant_id)
    if not is_running:
        return False, "该租户的机器人未在运行"
    
    pid_file = f"data/tenants/{tenant_id}/platforms/telegram/bot.pid"
    
    try:
        if sys.platform == 'win32':
            import psutil
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)
        else:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
        
        # 删除 PID 文件
        if os.path.exists(pid_file):
            os.remove(pid_file)
        
        return True, f"机器人已停止 (PID: {pid})"
    except Exception as e:
        return False, f"停止失败: {e}"


def read_file(filename, default=""):
    """读取文件内容"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return default
    except Exception as e:
        return f"读取失败: {e}"


def write_file(filename, content):
    """写入文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, "保存成功"
    except Exception as e:
        return False, f"保存失败: {e}"


def read_log_file(file_path, max_lines=100):
    try:
        if not os.path.exists(file_path):
            return "暂无日志文件"
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return "日志文件为空"
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if not lines:
                return "日志文件为空"
            return ''.join(lines[-max_lines:])
    except Exception as e:
        return f"读取日志失败: {e}"
def read_logs(max_lines=100):
    """读取最新的日志"""
    try:
        if not os.path.exists(BOT_LOG_FILE):
            return "暂无日志文件\n\n💡 提示：\n1. 点击侧边栏的 '启动' 按钮启动机器人\n2. 等待 2-3 秒后点击 '刷新' 按钮\n3. 如果仍无日志，检查 main.py 是否有错误"
        
        # 检查文件大小
        file_size = os.path.getsize(BOT_LOG_FILE)
        if file_size == 0:
            return "日志文件为空\n\n💡 提示：\n1. 机器人可能刚启动，请等待 2-3 秒\n2. 点击 '刷新' 按钮查看最新日志\n3. 如果持续为空，可能 main.py 启动失败"
        
        with open(BOT_LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if not lines:
                return "日志文件为空（未写入内容）"
            return ''.join(lines[-max_lines:])
    except Exception as e:
        return f"读取日志失败: {e}"


LOGIN_CONFIG_FILE = os.path.join('platforms', 'telegram', 'login_config.json')

def load_config():
    default = {"telegram": {"session": "", "phone": ""}}
    try:
        with open(LOGIN_CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'telegram' in data:
            return data
    except Exception:
        pass
    return default

def save_config(config):
    os.makedirs(os.path.dirname(LOGIN_CONFIG_FILE), exist_ok=True)
    with open(LOGIN_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=True, indent=2)

def get_login_client():
    from telethon import TelegramClient
    api_id = (os.getenv('TELEGRAM_API_ID') or "").strip()
    api_hash = (os.getenv('TELEGRAM_API_HASH') or "").strip()
    if (not api_id) or (not api_hash):
        return None, 'Missing TELEGRAM_API_ID/TELEGRAM_API_HASH in .env'
    if not api_id.isdigit():
        return None, 'Invalid TELEGRAM_API_ID in .env (must be digits)'
    admin_session = 'admin_session'
    if not os.path.exists(f'{admin_session}.session') and os.path.exists('userbot_session.session'):
        try:
            shutil.copy('userbot_session.session', f'{admin_session}.session')
        except Exception:
            pass
    client = TelegramClient(admin_session, int(api_id), api_hash, loop=ensure_event_loop())
    try:
        # Telethon's connect() is a coroutine, so we need to run it in the loop
        # But here we are in a synchronous context (Streamlit).
        # We can try to just return the client and let the caller handle connection,
        # OR we can synchronously wait for connection using the loop.
        
        loop = ensure_event_loop()
        loop.run_until_complete(client.connect())
        
    except Exception as exc:
        return None, f'Failed to connect Telegram client: {exc}'
    return client, None

def ensure_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop
# ===== Telegram Login UI =====
def init_login_state():
    if 'login_state' not in st.session_state:
        st.session_state.login_state = {"step": "phone", "phone": "", "code": "", "password": "", "message": ""}
    if 'show_login_panel' not in st.session_state:
        st.session_state.show_login_panel = False

def toggle_login_panel():
    st.session_state.show_login_panel = (not st.session_state.get('show_login_panel', False))

def render_login_panel(client=None, config=None):
    from telethon.errors import SessionPasswordNeededError
    init_login_state()
    if not st.session_state.show_login_panel:
        return
    if config is None:
        config = load_config()
    if client is None:
        client, client_err = get_login_client()
        if client_err:
            st.error(client_err)
            if st.button("🔎 查看缺失配置", key="diag_login"):
                missing, invalid = diagnose_env()
                if not missing and not invalid:
                    st.success("✅ 环境变量配置完整")
                else:
                    if missing:
                        st.error("❌ 缺少: " + ", ".join(missing))
                    if invalid:
                        st.error("❌ 格式错误: " + ", ".join(invalid))
            return
    state = st.session_state.login_state
    st.markdown("### \u767b\u5f55 Telegram")
    msg = state.get("message", "")
    if msg:
        st.info(msg)
    phone = st.text_input("\u624b\u673a\u53f7\u7801", value=state.get("phone", ""), placeholder="+86xxxxxxxxxx")
    state["phone"] = phone
    col1, col2 = st.columns(2)
    with col1:
        code = st.text_input("\u9a8c\u8bc1\u7801", value=state.get("code", ""))
    with col2:
        password = st.text_input("\u4e8c\u6b21\u5bc6\u7801", value=state.get("password", ""), type="password")
    state["code"] = code
    state["password"] = password
    if st.button("\u83b7\u53d6\u9a8c\u8bc1\u7801"):
        try:
            client.send_code_request(phone)
            state["step"] = "code"
            state["message"] = "\u9a8c\u8bc1\u7801\u5df2\u53d1\u9001"
        except Exception as e:
            state["message"] = f"\u53d1\u9001\u5931\u8d25: {e}"
    if st.button("\u767b\u5f55"):
        try:
            if state.get("step") == "code":
                client.sign_in(phone=phone, code=code)
            if state.get("step") == "password":
                client.sign_in(password=password)
            if client.is_user_authorized():
                config['telegram']['session'] = client.session.save()
                config['telegram']['phone'] = phone
                save_config(config)
                state["message"] = "\u767b\u5f55\u6210\u529f"
                st.session_state.show_login_panel = False
        except SessionPasswordNeededError:
            state["step"] = "password"
            state["message"] = "\u8bf7\u8f93\u5165\u4e8c\u6b21\u5bc6\u7801"
        except Exception as e:
            state["message"] = f"\u767b\u5f55\u5931\u8d25: {e}"

# ==================== Telethon 异步函数 ====================

async def get_telegram_folders():
    from telethon import TelegramClient
    from telethon.tl.functions.messages import GetDialogFiltersRequest
    from telethon.tl.types import DialogFilter
    """获取 Telegram 聊天分组"""
    try:
        TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
        TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
        
        if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH]):
            return None, "缺少 Telegram API 配置"
        
        # 使用独立的 admin session，避免与 main.py 冲突
        # 如果 admin session 不存在，复制 userbot_session
        admin_session = 'admin_session'
        if not os.path.exists(f'{admin_session}.session') and os.path.exists('userbot_session.session'):
            import shutil
            shutil.copy('userbot_session.session', f'{admin_session}.session')
        
        client = TelegramClient(admin_session, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        
        # 添加连接超时
        await asyncio.wait_for(client.connect(), timeout=10)
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return None, "未登录 Telegram，请先停止机器人，然后运行 main.py 登录"
        
        result = await client(GetDialogFiltersRequest())
        folders = []
        
        for folder in result:
            if isinstance(folder, DialogFilter):
                folders.append({
                    'id': folder.id,
                    'title': folder.title,
                    'folder': folder
                })
        
        await client.disconnect()
        return folders, "成功"
    except asyncio.TimeoutError:
        return None, "连接超时，请检查网络或重试"
    except Exception as e:
        error_msg = str(e)
        if 'database is locked' in error_msg:
            return None, "数据库被锁定，请先停止机器人后再使用群发功能"
        return None, f"获取分组失败: {e}"


async def get_chats_in_folder(folder):
    from telethon import TelegramClient
    """获取分组中的对话"""
    try:
        TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
        TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
        
        # 使用独立的 admin session
        client = TelegramClient('admin_session', int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        await asyncio.wait_for(client.connect(), timeout=10)
        
        chats = []
        all_dialogs = await client.get_dialogs()
        
        # 收集分组中的 peer IDs
        included_peer_ids = set()
        
        if hasattr(folder, 'pinned_peers') and folder.pinned_peers:
            for peer in folder.pinned_peers:
                try:
                    entity = await client.get_entity(peer)
                    included_peer_ids.add(entity.id)
                except:
                    pass
        
        if hasattr(folder, 'include_peers') and folder.include_peers:
            for peer in folder.include_peers:
                try:
                    entity = await client.get_entity(peer)
                    included_peer_ids.add(entity.id)
                except:
                    pass
        
        for dialog in all_dialogs:
            if dialog.entity.id in included_peer_ids:
                chats.append(dialog)
        
        await client.disconnect()
        return chats, "成功"
    except asyncio.TimeoutError:
        return None, "连接超时"
    except Exception as e:
        error_msg = str(e)
        if 'database is locked' in error_msg:
            return None, "数据库被锁定，请先停止机器人"
        return None, f"获取对话失败: {e}"


async def send_broadcast_async(chats, message, progress_callback):
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError, PeerFloodError
    """异步执行群发"""
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
    
    # 使用独立的 admin session
    client = TelegramClient('admin_session', int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
    await asyncio.wait_for(client.connect(), timeout=10)
    
    total = len(chats)
    success = 0
    failed = 0
    
    for idx, dialog in enumerate(chats):
        try:
            # 获取名称
            if hasattr(dialog.entity, 'title'):
                name = dialog.entity.title
            elif hasattr(dialog.entity, 'first_name'):
                name = dialog.entity.first_name
            else:
                name = "Unknown"
            
            progress_callback(idx + 1, total, f"正在发送给: {name}")
            
            await client.send_message(dialog.entity, message)
            success += 1
            
            # 随机延迟 5-10 秒
            if idx < total - 1:
                delay = random.uniform(5, 10)
                await asyncio.sleep(delay)
        
        except FloodWaitError as e:
            progress_callback(idx + 1, total, f"触发限流，等待 {e.seconds} 秒...")
            await asyncio.sleep(e.seconds)
            failed += 1
        
        except PeerFloodError:
            progress_callback(idx + 1, total, "检测到 PeerFlood，停止发送")
            failed += total - idx
            break
        
        except Exception as e:
            progress_callback(idx + 1, total, f"发送失败: {e}")
            failed += 1
    
    await client.disconnect()
    return success, failed


# ==================== 主界面 ====================

def main():
    init_login_state()
    # 标题
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="topbar-title">Telegram AI 中控台</div>
                <div class="topbar-sub">运营配置 · 群发管理 · 日志与监控</div>
            </div>
            <div class="topbar-meta">
                <span class="tag">版本 {APP_VERSION}</span>
                <span class="tag">Streamlit {st.__version__}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.title("⚙️ 控制面板")
        
        # 状态显示
        is_running, pid = get_bot_status()
        if is_running:
            st.markdown(f'<div class="status-running">🟢 运行中 (PID: {pid})</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-stopped">🔴 已停止</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # 控制按钮
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 启动", width="stretch", type="primary", disabled=is_running):
                success, message = start_bot()
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            if st.button("⛔ 停止", width="stretch", type="secondary", disabled=not is_running):
                success, message = stop_bot()
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
        
        st.divider()
        
        # 系统信息
        st.subheader("📊 系统信息")
        st.text(f"项目路径: {os.getcwd()}")
        st.text(f"Python: {sys.version.split()[0]}")
        
        if os.path.exists(".env"):
            st.success("✅ .env 配置完成")
        else:
            st.error("❌ 缺少 .env 文件")
        
        if os.path.exists("userbot_session.session"):
            st.success("✅ Telegram 已登录")
        else:
            st.warning("⚠️ 未登录 Telegram")
            if st.button("\u672a\u767b\u5f55 Telegram (\u70b9\u51fb\u767b\u5f55)"):
                toggle_login_panel()

        st.divider()
        if st.button("🔎 环境诊断", width="stretch"):
            missing, invalid = diagnose_env()
            if not missing and not invalid:
                st.success("✅ 环境变量配置完整")
            else:
                if missing:
                    st.error("❌ 缺少: " + ", ".join(missing))
                if invalid:
                    st.error("❌ 格式错误: " + ", ".join(invalid))
    
    # ==================== 主界面 Tab ====================
    with st.expander("Telegram \u767b\u5f55", expanded=st.session_state.get('show_login_panel', False)):
        render_login_panel()
    tab1, tab2, tab3 = st.tabs(["🧠 话术配置", "📢 消息群发", "📜 运行日志"])
    

# ==================== Tab 1: 话术配置 ====================
    with tab1:
        st.header("🧠 话术配置")
        st.caption("实时生效，无需重启机器人")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎭 AI 人设 (Prompt)")
            prompt_content = read_file("prompt.txt", "你是一个幽默、专业的个人助理。")
            new_prompt = st.text_area(
                "编辑 AI 人设",
                value=prompt_content,
                height=300,
                help="定义 AI 的性格和回复风格"
            )
            
            if st.button("💾 保存人设", width="stretch"):
                success, message = write_file("prompt.txt", new_prompt)
                if success:
                    st.success("✅ " + message)
                else:
                    st.error("❌ " + message)
        
        with col2:
            st.subheader("🔑 触发关键词 (Keywords)")
            keywords_content = read_file("keywords.txt", "帮我\n求助\nAI")
            new_keywords = st.text_area(
                "编辑触发关键词",
                value=keywords_content,
                height=300,
                help="每行一个关键词，用于群聊触发"
            )
            
            if st.button("💾 保存关键词", width="stretch"):
                success, message = write_file("keywords.txt", new_keywords)
                if success:
                    st.success("✅ " + message)
                else:
                    st.error("❌ " + message)
        
        st.divider()
        
        # ==================== 功能开关配置 ====================
        st.subheader("⚙️ 功能开关")
        
        # 读取当前配置
        config_content = read_file("config.txt", """# 个人消息回复开关
PRIVATE_REPLY=on

# 群消息回复开关
GROUP_REPLY=on""")
        
        # 解析配置
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
            st.markdown("**私聊消息回复**")
            private_reply = st.toggle(
                "开启私聊自动回复",
                value=current_config['PRIVATE_REPLY'],
                help="开启后，所有私聊消息都会自动回复"
            )
            if current_config['PRIVATE_REPLY']:
                st.success("✅ 当前状态：开启")
            else:
                st.error("🔴 当前状态：关闭")
        
        with col2:
            st.markdown("**群聊消息回复**")
            group_reply = st.toggle(
                "开启群聊自动回复",
                value=current_config['GROUP_REPLY'],
                help="开启后，根据关键词和@触发回复"
            )
            if current_config['GROUP_REPLY']:
                st.success("✅ 当前状态：开启")
            else:
                st.error("🔴 当前状态：关闭")
        
        # 保存开关配置
        if st.button("💾 保存开关设置", width="stretch", type="primary"):
            new_config = f"""# ========================================
# Telegram AI Bot - 功能开关配置
# ========================================
# 
# 说明：修改后立即生效，无需重启机器人
# 配置值：on 或 off（不区分大小写）
# ========================================

# 个人消息回复开关
# on = 开启（自动回复所有私聊消息）
# off = 关闭（不回复私聊消息）
PRIVATE_REPLY={'on' if private_reply else 'off'}

# 群消息回复开关
# on = 开启（根据关键词和@触发回复）
# off = 关闭（不回复群聊消息）
GROUP_REPLY={'on' if group_reply else 'off'}

# ========================================
# 其他配置（预留）
# ========================================

# 是否显示"正在输入"状态
# SHOW_TYPING=on

# 是否记录聊天日志
# LOG_MESSAGES=on
"""
            success, message = write_file("config.txt", new_config)
            if success:
                st.success("✅ " + message + " - 立即生效！")
            else:
                st.error("❌ " + message)
        
        st.divider()
        st.info("💡 提示：修改后立即生效，机器人会在下一条消息时使用新配置")
    
    # ==================== Tab 2: 消息群发 ====================
    with tab2:
        st.header("📢 消息群发")
        st.warning("⚠️ 频繁群发可能导致账号被限制，建议小批量测试（3-5条）")
        
        # 检查机器人运行状态
        is_bot_running, _ = get_bot_status()
        if is_bot_running:
            st.info("💡 提示：机器人正在运行中。如遇到数据库锁定错误，请先停止机器人再使用群发功能。")
        
        # 初始化 session state
        if 'folders' not in st.session_state:
            st.session_state.folders = None
        if 'selected_folder' not in st.session_state:
            st.session_state.selected_folder = None
        if 'chats' not in st.session_state:
            st.session_state.chats = None
        
        # 步骤 1: 加载分组
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("1️⃣ 选择目标分组")
        with col2:
            if st.button("🔄 加载分组", width="stretch"):
                with st.spinner("正在连接 Telegram..."):
                    try:
                        # 在新的事件循环中运行
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        folders, message = loop.run_until_complete(get_telegram_folders())
                        loop.close()
                        
                        if folders:
                            st.session_state.folders = folders
                            st.success(f"✅ 加载成功，找到 {len(folders)} 个分组")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ 加载失败: {e}")
        
        # 显示分组选择
        if st.session_state.folders:
            folder_names = [f"{f['title']}" for f in st.session_state.folders]
            selected_name = st.selectbox("选择分组", folder_names)
            
            if selected_name:
                selected_idx = folder_names.index(selected_name)
                st.session_state.selected_folder = st.session_state.folders[selected_idx]
                
                # 加载分组中的对话
                if st.button("📋 预览对话列表", width="stretch"):
                    with st.spinner("正在加载对话..."):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            chats, message = loop.run_until_complete(
                                get_chats_in_folder(st.session_state.selected_folder['folder'])
                            )
                            loop.close()
                            
                            if chats:
                                st.session_state.chats = chats
                                st.success(f"✅ 找到 {len(chats)} 个对话")
                                
                                # 显示前几个
                                with st.expander("查看目标列表"):
                                    for i, dialog in enumerate(chats[:10], 1):
                                        if hasattr(dialog.entity, 'title'):
                                            name = dialog.entity.title
                                        elif hasattr(dialog.entity, 'first_name'):
                                            name = dialog.entity.first_name
                                        else:
                                            name = "Unknown"
                                        st.text(f"{i}. {name}")
                                    
                                    if len(chats) > 10:
                                        st.text(f"... 还有 {len(chats) - 10} 个")
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"❌ 加载失败: {e}")
        
        st.divider()
        
        # 步骤 2: 输入消息
        st.subheader("2️⃣ 输入消息内容")
        message_content = st.text_area(
            "消息内容",
            placeholder="输入要群发的消息...",
            height=150
        )
        
        st.divider()
        
        # 步骤 3: 开始群发
        st.subheader("3️⃣ 开始群发")
        
        if not st.session_state.chats:
            st.info("请先加载分组和对话列表")
        elif not message_content.strip():
            st.info("请输入消息内容")
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"准备发送到 {len(st.session_state.chats)} 个对话")
            with col2:
                if st.button("🚀 开始群发", type="primary", width="stretch"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total, message):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.text(f"[{current}/{total}] {message}")
                    
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success, failed = loop.run_until_complete(
                            send_broadcast_async(
                                st.session_state.chats,
                                message_content,
                                update_progress
                            )
                        )
                        loop.close()
                        
                        # 显示结果
                        st.success(f"✅ 群发完成！成功: {success}, 失败: {failed}")
                    except Exception as e:
                        st.error(f"❌ 群发失败: {e}")
    
    # ==================== Tab 3: \u8fd0\u884c\u65e5\u5fd7 ====================
    with tab3:
        st.header("运行日志")
        st.caption("读取系统、私聊、群聊日志（日志中区分 QA_REPLY / AI_REPLY）")

        log_tab1, log_tab2, log_tab3 = st.tabs(["\u7cfb\u7edf\u65e5\u5fd7", "\u79c1\u804a\u65e5\u5fd7", "\u7fa4\u804a\u65e5\u5fd7"])

        def render_log_tab(tab_label, file_path, prefix, key_prefix):
            archive_files = list_archive_files(LOG_ARCHIVE_DIR, prefix)
            options = ["\u5f53\u524d\u65e5\u5fd7"] + [Path(p).name for p in archive_files]
            selected = st.selectbox("\u65e5\u5fd7\u6765\u6e90", options, key=f"{key_prefix}_source")
            target_path = file_path if selected == "\u5f53\u524d\u65e5\u5fd7" else str(Path(LOG_ARCHIVE_DIR) / selected)

            logs_preview = read_log_file(target_path, 300)
            st.text_area(tab_label, value=logs_preview, height=400, disabled=True, key=f"{key_prefix}_text")

            raw_logs = read_raw_log_file(target_path)
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("\u5237\u65b0", width="stretch", key=f"{key_prefix}_refresh"):
                    st.rerun()
            with col2:
                if st.button("\u5b58\u6863", width="stretch", key=f"{key_prefix}_archive"):
                    archived = archive_log_file(file_path, LOG_ARCHIVE_DIR, prefix)
                    if archived:
                        st.success("\u5df2\u5b58\u6863")
            with col3:
                if st.button("\u5b58\u6863\u5e76\u6e05\u7a7a", width="stretch", key=f"{key_prefix}_archive_clear"):
                    archive_and_clear_log(file_path, LOG_ARCHIVE_DIR, prefix)
                    st.success("\u5df2\u5b58\u6863\u5e76\u6e05\u7a7a")
                    st.rerun()
            with col4:
                filename = Path(target_path).name if target_path != file_path else f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                st.download_button(
                    "\u5bfc\u51fa",
                    data=raw_logs or "",
                    file_name=filename,
                    mime="text/plain",
                    width="stretch",
                    key=f"{key_prefix}_download",
                )

        with log_tab1:
            render_log_tab("\u7cfb\u7edf\u65e5\u5fd7", SYSTEM_LOG_FILE, "system", "system_log")
        with log_tab2:
            render_log_tab("\u79c1\u804a\u65e5\u5fd7", PRIVATE_LOG_FILE, "private", "private_log")
        with log_tab3:
            render_log_tab("\u7fa4\u804a\u65e5\u5fd7", GROUP_LOG_FILE, "group", "group_log")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        st.error(f"❌ 程序错误: {e}")
        import traceback
        st.code(traceback.format_exc())

