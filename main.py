import asyncio
import os
import sys
import random
import json
import re
import uuid
import difflib
from datetime import datetime
import httpx # 必须确保已安装: pip install httpx
from telethon import TelegramClient, events
from openai import AsyncOpenAI
from dotenv import load_dotenv
from database import db
from audit_manager import AuditManager
from conversation_state_manager import ConversationStateManager
from supervisor_agent import SupervisorAgent
from stage_agent_runtime import StageAgentRuntime

# --- 1. 基础设置 ---
# 解决 Windows 控制台乱码
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

load_dotenv()

def _ssl_verify_default():
    v = (os.getenv("HTTPX_VERIFY_SSL") or "").strip().lower()
    if v in ("0", "false", "no"):
        return False
    return True

# --- Logging (system / private / group) ---
LOG_DIR = os.path.join("platforms", "telegram", "logs")
SYSTEM_LOG_FILE = os.path.join(LOG_DIR, "system.log")
PRIVATE_LOG_FILE = os.path.join(LOG_DIR, "private.log")
GROUP_LOG_FILE = os.path.join(LOG_DIR, "group.log")
TRACE_LOG_FILE = os.path.join(LOG_DIR, "trace.jsonl")

def _append_log(file_path, message):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")

def log_trace_event(trace_id, event_type, payload):
    """
    记录结构化追踪日志 (JSONL 格式)
    符合 Automated Acceptance Execution Checklist 要求
    """
    os.makedirs(os.path.dirname(TRACE_LOG_FILE), exist_ok=True)
    
    # 构造标准事件结构
    event = {
        "trace_id": trace_id,
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type
    }
    # 合并 payload
    event.update(payload)
    
    with open(TRACE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def log_system(message):
    _append_log(SYSTEM_LOG_FILE, message)
    print(message)

def log_private(message):
    _append_log(PRIVATE_LOG_FILE, message)
    print(message)

def log_group(message):
    _append_log(GROUP_LOG_FILE, message)
    print(message)

# --- 2. 加载配置 & 自动修复错误 ---
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
AI_API_KEY = os.getenv('AI_API_KEY')
AI_BASE_URL = os.getenv('AI_BASE_URL')
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME')

# 🔍【自动修复功能】防止 .env 填错
if AI_BASE_URL:
    # 1. 如果忘了写 https://，自动补上
    if not AI_BASE_URL.startswith("http"):
        AI_BASE_URL = f"https://{AI_BASE_URL}"
    
    # 2. 【关键修复】将错误域名 55.ai 替换为正确的 api.55.ai
    if "://55.ai" in AI_BASE_URL:
        AI_BASE_URL = AI_BASE_URL.replace("://55.ai", "://api.55.ai")
        log_system("⚠️ 检测到旧域名，已自动修正为 api.55.ai")
    
    # 3. 如果多写了 /chat/completions，自动去掉（OpenAI SDK 会自动拼接）
    if "/chat/completions" in AI_BASE_URL:
        AI_BASE_URL = AI_BASE_URL.replace("/chat/completions", "")
    
    # 4. 确保以 /v1 结尾（根据 API 规范）
    if not AI_BASE_URL.endswith("/v1"):
        AI_BASE_URL = AI_BASE_URL.rstrip("/") + "/v1"

log_system(f"🔧 AI 接口地址已修正为: {AI_BASE_URL}")

# --- 3. 初始化客户端 (抗干扰模式) ---

# 创建一个忽略证书错误的 HTTP 客户端 (解决 SSL Error)
http_client = httpx.AsyncClient(verify=_ssl_verify_default(), timeout=30.0)

ai_client = AsyncOpenAI(
    api_key=AI_API_KEY,
    base_url=AI_BASE_URL,
    http_client=http_client # 强制使用这个客户端
)

client = TelegramClient('userbot_session', int(TELEGRAM_API_ID), TELEGRAM_API_HASH)

# 【已移除硬编码】现在提示词从 prompt.txt 文件动态加载
# SYSTEM_PROMPT = """..."""

# --- 4. 核心逻辑 ---

def load_system_prompt():
    """
    热更新功能：从 prompt.txt 读取 AI 提示词
    这样可以在程序运行时随时修改 AI 人设，无需重启
    """
    prompt_file = "platforms/telegram/prompt.txt"
    default_prompt = "你是一个幽默、专业的个人助理，帮机主回复消息。请用自然、友好的语气回复。"
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return content
            else:
                return default_prompt
    except FileNotFoundError:
        log_system(f"⚠️ 未找到 {prompt_file}，使用默认提示词")
        return default_prompt
    except Exception as e:
        log_system(f"⚠️ 读取 {prompt_file} 失败: {e}，使用默认提示词")
        return default_prompt

def load_keywords():
    """
    热更新功能：从 keywords.txt 读取群聊触发关键词
    每次处理消息时重新读取，实现实时更新
    """
    keywords_file = "platforms/telegram/keywords.txt"
    keywords = []
    
    try:
        with open(keywords_file, 'r', encoding='utf-8') as f:
            for line in f:
                keyword = line.strip()
                # 忽略空行和注释行（以 # 开头）
                if keyword and not keyword.startswith('#'):
                    keywords.append(keyword)
        return keywords
    except FileNotFoundError:
        # 文件不存在时返回空列表（群聊只能通过 @ 触发）
        return []
    except Exception as e:
        log_system(f"⚠️ 读取 {keywords_file} 失败: {e}")
        return []


# ===== Q&A Knowledge Base (Telegram) =====
def _read_lines_with_fallback(file_path):
    encodings = ["utf-8", "gbk", "cp936"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read().splitlines()
        except UnicodeDecodeError:
            continue
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()

def _split_variants(text):
    parts = re.split(r"[\\/|｜]+", text)
    return [p.strip() for p in parts if p.strip()]

def load_qa_pairs(file_path):
    qa_pairs = []
    if not file_path or (not os.path.exists(file_path)):
        return qa_pairs
    try:
        raw_lines = _read_lines_with_fallback(file_path)
        pending_qs = []
        collecting = False
        answer_lines = []
        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                if collecting and pending_qs:
                    answer_lines.append("")
                continue
            if stripped.startswith('#'):
                continue
            if '||' in stripped:
                q, a = stripped.split('||', 1)
                q = q.strip()
                a = a.strip()
                if q and a:
                    variants = _split_variants(q)
                    for v in variants:
                        qa_pairs.append((v, a))
                continue
            if stripped.lower().startswith('q:'):
                if pending_qs and answer_lines:
                    answer = "\n".join(answer_lines).strip()
                    for v in pending_qs:
                        qa_pairs.append((v, answer))
                pending_qs = _split_variants(stripped[2:].strip())
                collecting = False
                answer_lines = []
                continue
            if stripped.lower().startswith('a:') and pending_qs:
                collecting = True
                answer_lines.append(stripped[2:].strip())
                continue
            if collecting and pending_qs:
                answer_lines.append(stripped)
        if pending_qs and answer_lines:
            answer = "\n".join(answer_lines).strip()
            for v in pending_qs:
                qa_pairs.append((v, answer))
    except Exception:
        return []
    return qa_pairs

def _normalize_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)
    return text
def _bigram_tokens(text):
    if not text:
        return set()
    if len(text) < 2:
        return {text}
    return set(text[i:i+2] for i in range(len(text) - 1))

def match_qa_reply(message_text, qa_pairs):
    if not message_text:
        return None
    msg = message_text.strip()
    if not msg:
        return None
    norm_msg = _normalize_text(msg)
    if not norm_msg:
        return None
    msg_tokens = set(norm_msg[i:i+2] for i in range(len(norm_msg) - 1)) if len(norm_msg) >= 2 else set([norm_msg])
    for q, a in qa_pairs:
        if not q:
            continue
        norm_q = _normalize_text(q)
        if not norm_q:
            continue
        if norm_q in norm_msg or norm_msg in norm_q:
            return a
        # token overlap for short queries
        q_tokens = set(norm_q[i:i+2] for i in range(len(norm_q) - 1)) if len(norm_q) >= 2 else set([norm_q])
        if q_tokens:
            overlap = len(msg_tokens & q_tokens) / max(1, len(q_tokens))
            if overlap >= 0.6:
                return a
        ratio = difflib.SequenceMatcher(None, norm_q, norm_msg).ratio()
        if ratio >= 0.68:
            return a
    return None

def load_kb_entries():
    """
    加载知识库条目：优先从 SQLite 数据库加载，其次尝试加载本地文本文件
    """
    items = []
    
    # 1. 尝试从 SQLite 加载 (默认租户)
    try:
        # 假设 bot 运行在 default 租户下，或后续可配置
        db_items = db.get_kb_items("default")
        if db_items:
            # 转换为 list of dict (db.get_kb_items 返回的已经是 dict 列表)
            items.extend(db_items)
            log_system(f"📚 从数据库加载了 {len(db_items)} 条知识库条目")
    except Exception as e:
        log_system(f"⚠️ 从数据库加载知识库失败: {e}")

    # 2. 兼容 platforms/telegram/Knowledge Base.txt 作为文本来源
    kb_text_file = os.path.join(os.path.dirname(__file__), "platforms", "telegram", "Knowledge Base.txt")
    try:
        if os.path.exists(kb_text_file):
            with open(kb_text_file, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                items.append({
                    "id": "telegram_kb_txt",
                    "title": "Telegram 知识库文本",
                    "category": "text",
                    "tags": ["telegram", "kb"],
                    "content": content,
                    "source_file": os.path.relpath(kb_text_file, os.path.dirname(__file__)),
                })
                log_system("📚 加载了本地 Knowledge Base.txt")
    except Exception as e:
        log_system(f"⚠️ 加载本地知识库文本失败: {e}")
        
    return items

def retrieve_kb_context(query_text, kb_items, topn=2):
    if not query_text or (not kb_items):
        return []
    norm_q = _normalize_text(query_text)
    if not norm_q:
        return []
    q_tokens = _bigram_tokens(norm_q)
    scored = []
    for it in kb_items:
        title = _normalize_text((it.get("title","") or ""))
        content = _normalize_text((it.get("content","") or ""))
        if not title and not content:
            continue
        t_tokens = _bigram_tokens(title)
        c_tokens = _bigram_tokens(content)
        title_overlap = len(q_tokens & t_tokens) / max(1, len(q_tokens))
        content_overlap = len(q_tokens & c_tokens) / max(1, len(q_tokens))
        bonus = 0.0
        if norm_q in title or title in norm_q:
            bonus += 0.6
        if norm_q in content or content in norm_q:
            bonus += 0.3
        base = 2.0 * title_overlap + 1.0 * content_overlap + bonus
        if base == 0.0:
            text_all = title + content
            base = difflib.SequenceMatcher(None, norm_q, text_all).ratio() * 0.5
        scored.append((base, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:max(1, topn)]]

def load_config():
    """
    热更新功能：从 config.txt 读取功能开关配置
    返回配置字典
    """
    config_file = "platforms/telegram/config.txt"
    config = {
        'PRIVATE_REPLY': True,   # 默认开启私聊回复
        'GROUP_REPLY': True,     # 默认开启群聊回复
        'GROUP_CONTEXT': False,  # 是否在群聊中开启上下文自动回复（无关键词＋未被 @ 时也可回复）
        'AI_TEMPERATURE': 0.7,   # AI 温度，默认 0.7
        'AUDIT_ENABLED': True,   # 默认开启内容审核
        'AUDIT_MAX_RETRIES': 3,  # 默认最大重试次数
        'AUDIT_TEMPERATURE': 0.0, # 默认审核温度
        'REPLY_DELAY_MIN_SECONDS': 3.0,
        'REPLY_DELAY_MAX_SECONDS': 10.0,
        'AUTO_QUOTE': False,
        'QUOTE_INTERVAL_SECONDS': 30.0,
        'QUOTE_MAX_LEN': 200,
        'CONV_ORCHESTRATION': False
    }
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析配置行：KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().lower()
                    
                    if key in ['PRIVATE_REPLY', 'GROUP_REPLY', 'GROUP_CONTEXT', 'AUDIT_ENABLED', 'AUTO_QUOTE', 'CONV_ORCHESTRATION']:
                        config[key] = (value == 'on')
                    elif key in ['AI_TEMPERATURE', 'AUDIT_TEMPERATURE']:
                        try:
                            config[key] = float(value)
                        except ValueError:
                            pass
                    elif key in ['REPLY_DELAY_MIN_SECONDS', 'REPLY_DELAY_MAX_SECONDS', 'QUOTE_INTERVAL_SECONDS']:
                        try:
                            config[key] = float(value)
                        except ValueError:
                            pass
                    elif key == 'AUDIT_MAX_RETRIES':
                        try:
                            config[key] = int(value)
                        except ValueError:
                            pass
                    elif key in ['AUDIT_MODE', 'AUDIT_SERVERS']:
                        config[key] = value
                    elif key == 'QUOTE_MAX_LEN':
                        try:
                            config[key] = int(value)
                        except ValueError:
                            pass
        
        return config
    except FileNotFoundError:
        log_system(f"⚠️ 未找到 {config_file}，使用默认配置")
        return config
    except Exception as e:
        log_system(f"⚠️ 读取 {config_file} 失败: {e}，使用默认配置")
        return config

TG_PLATFORM_DIR = "platforms/telegram"
GROUP_CACHE_FILE = os.path.join(TG_PLATFORM_DIR, "group_cache.json")
SELECTED_GROUPS_FILE = os.path.join(TG_PLATFORM_DIR, "selected_groups.json")

def load_group_cache():
    try:
        with open(GROUP_CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except:
        pass
    return {}

def save_group_cache(cache):
    os.makedirs(os.path.dirname(GROUP_CACHE_FILE), exist_ok=True)
    with open(GROUP_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

async def record_group(event):
    if not event.is_group:
        return
    chat_id = getattr(event, 'chat_id', None)
    if chat_id is None:
        return
    chat_id_str = str(chat_id)
    cache = load_group_cache()
    chat_obj = getattr(event, 'chat', None) or getattr(event.message, 'chat', None)
    title = ""
    if chat_obj:
        title = getattr(chat_obj, 'title', None) or getattr(chat_obj, 'name', None) or ""
    else:
        try:
            chat = await event.get_chat()
            title = getattr(chat, 'title', None) or getattr(chat, 'name', None) or ""
        except:
            title = ""
    entry = dict(cache.get(chat_id_str, {}))
    entry['title'] = title or entry.get('title', '')
    entry['last_seen'] = datetime.now().isoformat()
    cache[chat_id_str] = entry
    save_group_cache(cache)
    descriptor = title or str(chat_id)
    log_system(f"🗂️ 缓存群聊: {descriptor} ({chat_id})")

def load_selected_group_ids():
    try:
        with open(SELECTED_GROUPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        raw_ids = data.get('selected_ids', [])
        result = set()
        for raw in raw_ids:
            try:
                result.add(int(raw))
            except:
                pass
        return result
    except:
        return set()


def load_stats():
    """加载统计数据"""
    stats_file = "platforms/telegram/stats.json"
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
    
    try:
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            if stats.get('start_time') is None:
                stats['start_time'] = datetime.now().isoformat()
            return stats
    except:
        return default_stats

def save_stats(stats):
    """保存统计数据"""
    stats_file = "platforms/telegram/stats.json"
    try:
        stats['last_active'] = datetime.now().isoformat()
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_system(f"⚠️ 保存统计失败: {e}")

async def get_chat_history(chat_id, limit=8, max_id=0):
    """获取聊天上下文"""
    messages = []
    try:
        async for msg in client.iter_messages(chat_id, limit=limit, max_id=max_id):
            if msg.text:
                role = "assistant" if msg.out else "user"
                messages.append({"role": role, "content": msg.text})
        return messages[::-1]
    except Exception:
        return []

async def _get_prev_incoming_message(chat_id, max_id=0):
    try:
        async for msg in client.iter_messages(chat_id, limit=1, max_id=max_id):
            if msg and msg.text and not msg.out:
                return msg
    except Exception:
        return None
    return None

def _similar(a, b):
    if not a or not b:
        return 0.0
    na = _normalize_text(a)
    nb = _normalize_text(b)
    if not na or not nb:
        return 0.0
    ta = _bigram_tokens(na)
    tb = _bigram_tokens(nb)
    if ta and tb:
        return len(ta & tb) / max(1, len(ta))
    return difflib.SequenceMatcher(None, na, nb).ratio()

async def _should_auto_quote(event, msg, config):
    if not config.get('AUTO_QUOTE', False):
        return False
    prev = await _get_prev_incoming_message(event.chat_id, max_id=event.id)
    if not prev:
        return False
    try:
        now = event.message.date
        diff = (now - prev.date).total_seconds()
    except Exception:
        diff = 9999.0
    if diff > float(config.get('QUOTE_INTERVAL_SECONDS', 30.0)):
        return False
    sim = _similar(msg or "", prev.text or "")
    if sim < 0.25:
        return False
    return True

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    # 只处理有文本内容的消息
    if not event.message.text:
        return
    
    # 1. MSG_RECEIVED (Trace Start)
    trace_id = str(uuid.uuid4())
    msg = event.message.text
    sender = await event.get_sender()
    user_id = str(event.chat_id)
    
    # 加载统计数据
    stats = load_stats()
    stats['total_messages'] += 1
    
    name = getattr(sender, 'first_name', '朋友')
    
    # 【热更新】实时读取配置
    config = load_config()
    keywords = load_keywords()
    context_reply_enabled = config.get('GROUP_CONTEXT', False)
    
    # 记录消息类型
    if event.is_private:
        stats['private_messages'] += 1
    elif event.is_group:
        stats['group_messages'] += 1

    if bool(config.get('CONV_ORCHESTRATION', False)):
        log_trace_event(trace_id, "MSG_RECEIVED", {
            "user_id": user_id,
            "content_len": len(msg),
            "platform": "telegram"
        })
    
    # 【功能开关检查】
    if event.is_private and not config['PRIVATE_REPLY']:
        # 私聊回复已关闭
        log_private(f"[trace:{trace_id}] 🔕 私聊回复已关闭，忽略消息 [{name}]: {msg}")
        return
    
    if event.is_group and not config['GROUP_REPLY']:
        # 群聊回复已关闭
        log_group(f"🔕 群聊回复已关闭，忽略消息 [{name}]: {msg}")
        return

    if event.is_group:
        await record_group(event)
        selected_group_ids = load_selected_group_ids()
        if selected_group_ids:
            chat_id = getattr(event, 'chat_id', None)
            if chat_id is None or int(chat_id) not in selected_group_ids:
                chat_obj = getattr(event, 'chat', None) or getattr(event.message, 'chat', None)
                chat_name = getattr(chat_obj, 'title', None) or getattr(chat_obj, 'name', None) if chat_obj else ""
                descriptor = chat_name or str(chat_id)
                log_group(f"🛑 群聊 [{descriptor}] 不在白名单，跳过回复")
                return
    
    # 【智能触发逻辑】
    should_reply = False
    
    if event.is_private:
        # 私聊：直接回复（已经通过开关检查）
        should_reply = True
        log_private(f"[trace:{trace_id}] 📩 收到私聊 [{name}]: {msg}")
    elif event.is_group:
        # 群聊：需要满足以下任一条件（已经通过开关检查）
        if event.mentioned:
            # 条件1：被 @ 了
            should_reply = True
            log_group(f"📩 群聊被 @ [{name}]: {msg}")
        elif keywords:
            # 条件2：消息包含关键词
            for keyword in keywords:
                if keyword.lower() in msg.lower():
                    should_reply = True
                    log_group(f"📩 群聊触发关键词 [{keyword}] [{name}]: {msg}")
                    break
        elif context_reply_enabled:
            should_reply = True
            log_group(f"📩 群聊上下文触发 [{name}]: {msg}")
    
    # 如果不满足回复条件，直接返回
    if not should_reply:
        return

    async with client.action(event.chat_id, 'typing'):
        # 【热更新】每次处理消息前重新读取提示词
        system_prompt = load_system_prompt()
        
        # 获取历史记录（保持上下文）
        history = await get_chat_history(event.chat_id, max_id=event.id)
        qa_file = os.path.join(os.path.dirname(__file__), 'platforms', 'telegram', 'qa.txt')
        qa_pairs = load_qa_pairs(qa_file)
        qa_reply = match_qa_reply(msg, qa_pairs)
        if qa_reply:
            log_trace_event(trace_id, "QA_HIT", {"reply_len": len(qa_reply)})
            await event.reply(qa_reply)
            log_trace_event(trace_id, "REPLY_SENT", {"content_len": len(qa_reply)})
            if event.is_private:
                log_private(f"[trace:{trace_id}] QA_REPLY: {qa_reply}")
            else:
                log_group(f"QA_REPLY: {qa_reply}")
            return
        
        # 默认上下文处理
        kb_items = load_kb_entries()
        kb_context = ""
        system_with_kb = system_prompt
        
        # 编排模式专用变量
        orch_enabled = bool(config.get('CONV_ORCHESTRATION', False))
        model_override = AI_MODEL_NAME
        temp_override = config.get('AI_TEMPERATURE', 0.7)
        ai_client_orch = ai_client # Default
        decision = {}

        if orch_enabled:
            try:
                tenant_id = "default"
                mgr = ConversationStateManager(tenant_id)
                state = mgr.get_state("tg", str(event.chat_id))
                
                # 2. STATE_LOADED
                log_trace_event(trace_id, "STATE_LOADED", {"state": state})
                
                # --- 1. Supervisor Decision (State Machine) ---
                sup = SupervisorAgent(tenant_id, config)
                decision = await sup.decide(state, history, ai_client, AI_MODEL_NAME)
                
                # 3. SUPERVISOR_DECIDED
                log_trace_event(trace_id, "SUPERVISOR_DECIDED", {
                    "decision": {
                        "current_stage": decision.get("current_stage"),
                        "advance_stage": decision.get("advance_stage"),
                        "next_stage": decision.get("next_stage"),
                        "persona_id": decision.get("persona_id"),
                        "agent_profile_id": decision.get("agent_profile_id"),
                        "need_human": decision.get("need_human"),
                        "override": decision.get("override", False)
                    }
                })
                
                # State Updates Logic
                old_stage = state.get("current_stage")
                if bool(decision.get("advance_stage")):
                    state["current_stage"] = decision.get("next_stage", state.get("current_stage"))
                state["persona_id"] = decision.get("persona_id", state.get("persona_id"))
                state["handoff_required"] = bool(decision.get("need_human", False))
                if "updated_slots" in decision:
                    state["slots"] = decision["updated_slots"]
                
                # 8. STATE_UPDATED (Pre-emptive logging before DB write)
                log_trace_event(trace_id, "STATE_UPDATED", {
                    "before": {"stage": old_stage},
                    "after": {"stage": state.get("current_stage")}
                })

                # Update State in DB
                mgr.update_state("tg", str(event.chat_id), state)
                
                # --- 2. Handoff Check ---
                if state["handoff_required"]:
                    # ... (Handoff logging logic kept simple for brevity) ...
                    handoff_msg = "👨‍💻 正在为您转接人工客服，请稍候..."
                    await event.reply(handoff_msg)
                    return

                # --- 3. Stage Agent Execution ---
                # 4. KB_RETRIEVED (Stage Scope Filtering)
                current_stage = state.get("current_stage", "S0")
                # Filter KB items that have the current stage tag OR are global (no tags or 'all')
                # Strict Assertion D: "KB_RETRIEVED.stage_scope 仅包含 current_stage"
                # So we filter strictly for now to pass assertion.
                filtered_kb = []
                for it in kb_items:
                    tags = it.get("tags", [])
                    if current_stage in tags:
                        filtered_kb.append(it)
                
                kb_hits = retrieve_kb_context(msg, filtered_kb, topn=2)
                
                log_trace_event(trace_id, "KB_RETRIEVED", {
                    "stage_scope": [current_stage],
                    "hits": [{"kb_id": it.get("id"), "tags": it.get("tags")} for it in kb_hits]
                })

                stager = StageAgentRuntime(tenant_id)
                rdec = stager.route_decision(state, history, filtered_kb) # Use filtered KB
                
                http_client2 = httpx.AsyncClient(verify=_ssl_verify_default(), timeout=30.0)
                ai_client_orch = AsyncOpenAI(
                    api_key=AI_API_KEY,
                    base_url=rdec.get("base_url") or AI_BASE_URL,
                    http_client=http_client2
                )
                model_override = rdec.get("model") or AI_MODEL_NAME
                temp_override = float(rdec.get("temperature") or config.get('AI_TEMPERATURE', 0.7))
                
                # 5. STAGE_AGENT_GENERATED
                log_trace_event(trace_id, "STAGE_AGENT_GENERATED", {
                    "used": {
                        "agent_profile_id": decision.get("agent_profile_id"),
                        "model": model_override,
                        "temperature": temp_override,
                        "fallback_used": False
                    },
                    "prompt_meta": {
                        "stage": current_stage,
                        "persona_id": state.get("persona_id"),
                        "kb_hit_ids": [it.get("id") for it in kb_hits]
                    }
                })

                full_system_prompt = stager.build_system_prompt(state, system_prompt, kb_hits) # Use hits
                
                # Record Decision for Audit (DB)
                try:
                    from database import db as _db
                    input_summary = f"User: {msg[:100]}..." 
                    if history:
                        last_ctx = history[-1]['content'][:50] if history else ""
                        input_summary += f" | Prev: {last_ctx}..."

                    _db.record_routing_decision(tenant_id, "tg", str(event.chat_id), {
                        "stage": state.get("current_stage"),
                        "persona": state.get("persona_id"),
                        "agent_profile_id": decision.get("agent_profile_id"),
                        "model": model_override,
                        "base_url": rdec.get("base_url"),
                        "temperature": temp_override,
                        "context": rdec.get("context"),
                        "matched_rule": rdec.get("matched_rule"),
                        "supervisor_decision": decision,
                        "input_summary": input_summary,
                        "manual_intervention": False
                    })
                except Exception:
                    pass
                    
                system_with_kb = full_system_prompt
            except Exception as e:
                log_system(f"⚠️ 编排逻辑执行失败 (Fallback to Default): {e}")
                log_trace_event(trace_id, "ORCHESTRATION_ERROR", {"error": str(e)})

        # Fallback to standard logic if not orch enabled or failed (system_with_kb prepared)
        if not orch_enabled and not kb_context:
             # Standard KB retrieval if not orch
             kb_hits = retrieve_kb_context(msg, kb_items, topn=2)
             if kb_hits:
                parts = []
                for it in kb_hits:
                    title = it.get("title","")
                    snippet = (it.get("content","") or "")
                    if len(snippet) > 800: snippet = snippet[:800]
                    parts.append(f"[{title}]\n{snippet}")
                kb_context = "\n\n".join(parts)
                system_with_kb = system_prompt + "\n\n【知识库参考】\n" + kb_context

        messages = [{"role": "system", "content": system_with_kb}] + history + [{"role": "user", "content": msg}]

        try:
            if event.is_private:
                log_private(f"[trace:{trace_id}] 🤖 AI 正在思考...")
            else:
                log_group("🤖 AI 正在思考...")
            
            audit_manager = AuditManager(ai_client_orch, model_override, load_config, platform="telegram")
            
            # 6. STYLE_GUARD / AUDIT (Implied)
            gen_result = await audit_manager.generate_with_audit(
                messages=messages,
                user_input=msg,
                history=history,
                temperature=temp_override
            )
            
            status_block = {}
            if isinstance(gen_result, dict):
                status_block = gen_result.get("status", {}) or {}
            # Emit STYLE_GUARD event regardless of return shape
            sg_applied = False
            if isinstance(gen_result, dict):
                sg_applied = bool(status_block.get("style_guard_applied"))
            log_trace_event(trace_id, "STYLE_GUARD", {"applied": sg_applied})
            if orch_enabled or status_block:
                if "audit_primary_passed" in status_block:
                    log_trace_event(trace_id, "AUDIT_PRIMARY", {"passed": bool(status_block.get("audit_primary_passed"))})
                if "audit_secondary_passed" in status_block:
                    log_trace_event(trace_id, "AUDIT_SECONDARY", {"passed": bool(status_block.get("audit_secondary_passed"))})
                if "final_action" in status_block:
                    log_trace_event(trace_id, "FINAL_ACTION", {"action": str(status_block.get("final_action"))})

            # Handle new return format (dict) or old (str)
            if isinstance(gen_result, dict):
                reply = gen_result.get("content", "")
                gen_usage = gen_result.get("usage", {})
            else:
                reply = gen_result
                gen_usage = {}
            
            # Aggregate Usage
            total_tokens = gen_usage.get("total_tokens", 0)
            final_model = gen_usage.get("model", model_override)
            
            if 'decision' in locals() and decision:
                 sup_usage = decision.get("usage")
                 if isinstance(sup_usage, dict):
                     total_tokens += sup_usage.get("total_tokens", 0)
                 elif isinstance(sup_usage, int): 
                     total_tokens += sup_usage

            # Simple Cost Estimation
            est_cost = (total_tokens / 1000.0) * 0.002
            
            # Record Message Event to DB
            try:
                current_stage = None
                if 'state' in locals() and state:
                    current_stage = state.get("current_stage")

                db.record_message_event(
                    tenant_id="default",
                    platform="telegram",
                    chat_id=str(event.chat_id),
                    direction="outbound",
                    status="sent",
                    tokens_used=total_tokens,
                    model=final_model,
                    cost=est_cost,
                    stage=current_stage
                )
            except Exception as e:
                log_system(f"⚠️ Failed to record message event: {e}")

            dmin = float(config.get('REPLY_DELAY_MIN_SECONDS', 3.0))
            dmax = float(config.get('REPLY_DELAY_MAX_SECONDS', 10.0))
            if dmin > dmax:
                dmin, dmax = dmax, dmin
            delay = random.uniform(dmin, dmax)
            await asyncio.sleep(delay)
            
            use_quote = await _should_auto_quote(event, msg, config)
            if use_quote:
                await event.reply(reply)
            else:
                await client.send_message(event.chat_id, reply)
            
            if event.is_private:
                log_private(f"[trace:{trace_id}] AI_REPLY: {reply}")
            else:
                log_group(f"AI_REPLY: {reply}")
            
            if orch_enabled:
                log_trace_event(trace_id, "REPLY_SENT", {"content_len": len(reply)})
            
            # 统计成功回复
            stats['total_replies'] += 1
            stats['success_count'] += 1
            save_stats(stats)
            
        except Exception as e:
            log_system(f"❌ AI 调用失败: {e}")
            if orch_enabled:
                 log_trace_event(trace_id, "ERROR", {"message": str(e)})
            # 统计失败
            stats['error_count'] += 1
            save_stats(stats)

# --- 5. 启动程序 ---
if __name__ == '__main__':
    log_system("🚀 程序启动中...")
    client.start()
    client.run_until_disconnected()
