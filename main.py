import asyncio
import os
import sys
import shutil
import random
import json
import re
import uuid
import difflib
from datetime import datetime
import httpx # 必须确保已安装: pip install httpx
from telethon import TelegramClient, events
from openai import AsyncOpenAI, APIConnectionError
from dotenv import load_dotenv

# --- Auto-setup Environment ---
# If .env is missing, try to create it from .env.example
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
_env_example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.example')
if not os.path.exists(_env_path) and os.path.exists(_env_example_path):
    try:
        shutil.copy(_env_example_path, _env_path)
        print(f"⚠️ 检测到 .env 缺失，已根据 .env.example 自动生成: {_env_path}")
    except Exception as e:
        print(f"❌ 无法自动生成 .env: {e}")

load_dotenv()

# --- Env Validation ---
if not os.getenv('TELEGRAM_API_ID'):
    print("================================================================")
    print("❌ 错误: 未检测到 TELEGRAM_API_ID")
    print("⚠️ 请打开 .env 文件，填写您的 Telegram API 配置和 AI 密钥")
    print("================================================================")
    sys.exit(1)

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

# 创建客户端的惰性初始化，避免在被其他线程导入时缺失事件循环
http_client = None
ai_client = None

def get_ai_client():
    global http_client, ai_client
    if ai_client is None or http_client is None:
        ssl_mode = _ssl_verify_default()
        log_system(f"🔌 初始化 AI 客户端: SSL验证={ssl_mode}")
        http_client = httpx.AsyncClient(verify=ssl_mode, timeout=30.0)
        ai_client = AsyncOpenAI(
            api_key=AI_API_KEY,
            base_url=AI_BASE_URL,
            http_client=http_client
        )
    return ai_client

def reset_ai_client():
    global http_client, ai_client
    http_client = None
    ai_client = None
    log_system("🔄 AI 客户端已重置 (准备重新初始化)")

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
            if overlap >= 0.45:
                return a
        ratio = difflib.SequenceMatcher(None, norm_q, norm_msg).ratio()
        if ratio >= 0.5:
            return a
    return None

def _set_kb_refresh_off():
    try:
        path = os.path.join("platforms", "telegram", "config.txt")
        if not os.path.exists(path): return
        with open(path, "r", encoding="utf-8") as f: lines = f.readlines()
        with open(path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip().startswith("KB_REFRESH="):
                    f.write("KB_REFRESH=off\n")
                else:
                    f.write(line)
        log_system("✅ KB_REFRESH 已自动重置为 off")
    except Exception as e:
        log_system(f"⚠️ 重置 KB_REFRESH 失败: {e}")

def load_kb_entries():
    """
    加载知识库条目：优先从 SQLite 数据库加载
    支持 KB_REFRESH=on 强制刷新
    如果数据库为空，则尝试从本地 Knowledge Base.txt 自动解析并导入
    """
    items = []
    
    try:
        # 0. 检查刷新指令或异常状态
        config = load_config()
        kb_refresh = str(config.get("KB_REFRESH", "off")).lower() == "on"
        need_reload = kb_refresh

        # 如果未强制刷新，先检查数据库状态
        if not need_reload:
            db_items = db.get_kb_items("default")
            # 异常检测：只有1条记录且内容极长（>2000字符），通常是错误的整本导入
            if db_items and len(db_items) == 1 and len(db_items[0].get("content", "")) > 2000:
                log_system("⚠️ 检测到知识库结构异常（单条过长），触发自动修复重置...")
                need_reload = True
            elif db_items:
                # 正常加载
                for it in db_items:
                    if isinstance(it.get("tags"), str):
                        try:
                            it["tags"] = json.loads(it["tags"])
                        except:
                            it["tags"] = [t.strip() for t in it["tags"].split(",") if t.strip()]
                items.extend(db_items)
                log_system(f"📚 从数据库加载了 {len(items)} 条知识库条目")

        # 1. 执行重置
        if need_reload:
            log_system("🔄 执行知识库重置 (KB_REFRESH/AutoFix)...")
            db.execute_update("DELETE FROM knowledge_base WHERE tenant_id = ?", ("default",))
            items = [] # 确保为空，触发下方导入逻辑
            if kb_refresh:
                _set_kb_refresh_off()

        # 2. 如果数据库为空（或已重置），执行导入
        if not items:
            kb_text_file = os.path.join(os.path.dirname(__file__), "platforms", "telegram", "Knowledge Base.txt")
            if os.path.exists(kb_text_file):
                try:
                    with open(kb_text_file, "r", encoding="utf-8-sig") as f:
                        content = f.read()
                    
                    if content.strip():
                        log_system("📂 正在解析并导入本地知识库...")
                        blocks = _parse_multi_lang_qa(content)
                        md_blocks = []
                        if not blocks:
                            md_blocks = _parse_markdown_kb(content)
                        
                        count = 0
                        ts = datetime.now().isoformat()
                        
                        if blocks:
                            for b in blocks:
                                q_sc = b.get('q_sc', '')
                                q_tc = b.get('q_tc', '')
                                a_sc = b.get('a_sc', '')
                                a_tc = b.get('a_tc', '')
                                
                                # 构造更丰富的检索内容
                                full_content = f"Question: {q_sc}\nQuestion_TC: {q_tc}\nAnswer: {a_sc}\nAnswer_TC: {a_tc}"
                                
                                new_id = str(uuid.uuid4())
                                new_item = {
                                    "id": new_id,
                                    "tenant_id": "default",
                                    "title": q_sc[:100] if q_sc else "无标题QA",
                                    "category": "qa",
                                    "tags": json.dumps(["telegram", "kb", "parsed"], ensure_ascii=False),
                                    "content": full_content,
                                    "source_file": "platforms/telegram/Knowledge Base.txt",
                                    "created_at": ts,
                                    "updated_at": ts
                                }
                                db.add_kb_item(new_item)
                                
                                # Add to memory
                                new_item["tags"] = ["telegram", "kb", "parsed"]
                                items.append(new_item)
                                count += 1
                            
                            log_system(f"✅ 成功导入 {count} 条 QA 知识库条目！")
                        elif md_blocks:
                            log_system("⚠️ QA解析为空，采用 Markdown 标题分割导入...")
                            for mb in md_blocks:
                                new_id = str(uuid.uuid4())
                                new_item = {
                                    "id": new_id,
                                    "tenant_id": "default",
                                    "title": mb['title'][:100],
                                    "category": "markdown",
                                    "tags": json.dumps(["telegram", "kb", "markdown"], ensure_ascii=False),
                                    "content": mb['content'],
                                    "source_file": "platforms/telegram/Knowledge Base.txt",
                                    "created_at": ts,
                                    "updated_at": ts
                                }
                                db.add_kb_item(new_item)
                                new_item["tags"] = ["telegram", "kb", "markdown"]
                                items.append(new_item)
                                count += 1
                            log_system(f"✅ 成功导入 {count} 条 Markdown 知识库条目！")
                        else:
                             # Fallback: 如果解析失败但文件不为空，仍尝试整本导入（避免完全无数据）
                             log_system("⚠️ 解析结果为空，执行整本导入(Fallback)...")
                             new_id = str(uuid.uuid4())
                             new_item = {
                                "id": new_id,
                                "tenant_id": "default",
                                "title": "默认知识库 (Fallback)",
                                "category": "text",
                                "tags": json.dumps(["telegram", "kb", "fallback"], ensure_ascii=False),
                                "content": content,
                                "source_file": "platforms/telegram/Knowledge Base.txt",
                                "created_at": ts,
                                "updated_at": ts
                             }
                             db.add_kb_item(new_item)
                             new_item["tags"] = ["telegram", "kb", "fallback"]
                             items.append(new_item)

                except Exception as e:
                    log_system(f"❌ 初始化导入失败: {e}")

            # 3. 尝试导入 qa.txt (如果存在且数据库为空/重置)
            qa_file = os.path.join(os.path.dirname(__file__), "platforms", "telegram", "qa.txt")
            if os.path.exists(qa_file):
                try:
                    with open(qa_file, "r", encoding="utf-8") as f:
                        qa_content = f.read()
                    
                    if qa_content.strip():
                        log_system("📂 正在解析并导入 qa.txt (补充知识库)...")
                        qa_blocks = _parse_multi_lang_qa(qa_content)
                        
                        if qa_blocks:
                            qa_count = 0
                            ts = datetime.now().isoformat()
                            for b in qa_blocks:
                                q_sc = b.get('q_sc', '')
                                q_tc = b.get('q_tc', '')
                                a_sc = b.get('a_sc', '')
                                a_tc = b.get('a_tc', '')
                                
                                full_content = f"Question: {q_sc}\nQuestion_TC: {q_tc}\nAnswer: {a_sc}\nAnswer_TC: {a_tc}"
                                
                                new_id = str(uuid.uuid4())
                                new_item = {
                                    "id": new_id,
                                    "tenant_id": "default",
                                    "title": q_sc[:100] if q_sc else "QA Pair",
                                    "category": "qa_txt",
                                    "tags": json.dumps(["telegram", "kb", "qa_txt"], ensure_ascii=False),
                                    "content": full_content,
                                    "source_file": "platforms/telegram/qa.txt",
                                    "created_at": ts,
                                    "updated_at": ts
                                }
                                db.add_kb_item(new_item)
                                items.append(new_item)
                                qa_count += 1
                            log_system(f"✅ 成功从 qa.txt 导入 {qa_count} 条知识库条目！")
                except Exception as e:
                    log_system(f"⚠️ 导入 qa.txt 失败: {e}")

            # 4. 尝试导入 extra_kb.txt (如 PDF 导入内容)
            extra_file = os.path.join(os.path.dirname(__file__), "platforms", "telegram", "extra_kb.txt")
            if os.path.exists(extra_file):
                try:
                    with open(extra_file, "r", encoding="utf-8") as f:
                        extra_content = f.read()
                    
                    if extra_content.strip():
                        log_system("📂 正在解析并导入 extra_kb.txt (额外知识库)...")
                        # 优先尝试 Markdown 解析
                        extra_blocks = _parse_markdown_kb(extra_content)
                        
                        extra_count = 0
                        ts = datetime.now().isoformat()
                        
                        if extra_blocks:
                            for mb in extra_blocks:
                                new_id = str(uuid.uuid4())
                                new_item = {
                                    "id": new_id,
                                    "tenant_id": "default",
                                    "title": mb['title'][:100],
                                    "category": "markdown",
                                    "tags": json.dumps(["telegram", "kb", "extra"], ensure_ascii=False),
                                    "content": mb['content'],
                                    "source_file": "platforms/telegram/extra_kb.txt",
                                    "created_at": ts,
                                    "updated_at": ts
                                }
                                db.add_kb_item(new_item)
                                items.append(new_item)
                                extra_count += 1
                            log_system(f"✅ 成功从 extra_kb.txt 导入 {extra_count} 条 Markdown 知识库条目！")
                        else:
                             # Fallback to full content
                             log_system("⚠️ extra_kb.txt 解析结果为空，执行整本导入...")
                             new_id = str(uuid.uuid4())
                             new_item = {
                                "id": new_id,
                                "tenant_id": "default",
                                "title": "额外知识库 (Full)",
                                "category": "text",
                                "tags": json.dumps(["telegram", "kb", "extra", "fallback"], ensure_ascii=False),
                                "content": extra_content,
                                "source_file": "platforms/telegram/extra_kb.txt",
                                "created_at": ts,
                                "updated_at": ts
                             }
                             db.add_kb_item(new_item)
                             items.append(new_item)
                             log_system("✅ 成功从 extra_kb.txt 导入整本内容")

                except Exception as e:
                    log_system(f"⚠️ 导入 extra_kb.txt 失败: {e}")

    except Exception as e:
        log_system(f"⚠️ 加载知识库失败: {e}")
        
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

def _split_sentences(s):
    if not s:
        return []
    parts = re.split(r"[。！？!?\n]+", s)
    return [p.strip() for p in parts if p.strip()]

def _is_single_point_question(text):
    if not text:
        return False
    t = text.strip()
    if len(t) <= 2:
        return False
    if re.search(r"(是什么|怎么算|如何|是否|费用|价格|收费|流程|规则|计算|怎么算|怎么计算)", t):
        if not re.search(r"(、|以及|和|并且)", t):
            return True
    return False

def _is_clear_question(text):
    if not text:
        return False
    t = text.strip()
    if len(t) < 6:
        return False
    if re.search(r"[?？]", t):
        return True
    if re.search(r"(怎么|如何|是否|多少|为什么|为什麼|規則|规则|計算|计算|流程|价格|費用|费用|收费)", t):
        return True
    return False

def _kb_is_qa_like(item):
    cat = (item.get("category","") or "").lower()
    title = (item.get("title","") or "").lower()
    tags = item.get("tags", [])
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = [tags]
    tlist = [str(x).lower() for x in tags] if isinstance(tags, list) else []
    qa_keys = ["客服话术","q&a","qa","faq","问答","话术"]
    for k in qa_keys:
        if k in cat or k in title or any(k in str(tx) for tx in tlist):
            return True
    return False

def detect_qa_only(query_text, kb_hits):
    reason = {}
    if not _is_clear_question(query_text or ""):
        return False, {}
    if kb_hits:
        if any(_kb_is_qa_like(it) for it in kb_hits):
            reason["kb_doc_type"] = True
    if _is_single_point_question(query_text or ""):
        reason["single_clear_question"] = True
    if not reason:
        return False, {}
    return True, reason

def _filter_sentences_by_user(text, user_text):
    sents = _split_sentences(text)
    if not sents:
        return text
    u = _normalize_text(user_text or "")
    utoks = _bigram_tokens(u)
    kept = []
    for s in sents:
        ns = _normalize_text(s)
        stoks = _bigram_tokens(ns)
        overlap = len(utoks & stoks) / max(1, len(stoks))
        if overlap >= 0.15 or (re.search(r"\d", s) or "%" in s):
            kept.append(s)
    if not kept:
        kept = sents
    return "。".join(kept) + ("。" if kept else "")

def build_qa_only_guidance():
    return (
        "必须使用 QA_ONLY 模式：仅回答当前问题；最多一个答案块；"
        "答案结构为1句结论，可选1-3句补充；禁止扩展到未被问及的问题；"
        "禁止输出文档标题、目录、页码、版权、Q:/A: 原始格式；"
        "如出现多个不同问题点或未在问题中的核心关键词，自动压缩，仅保留最相关内容；"
        "数值/规则类问题优先给出明确结论与必要说明，避免背景铺垫。"
    )

def build_conversation_mode_guidance(mode):
    if mode == 'human_simulated':
        return (
            "【重要指令】你现在必须完全模拟真人进行回复。"
            "1. 禁止自称“系统”、“AI”、“机器人”或“官方客服”。"
            "2. 禁止使用“记录”、“技术专家”、“反馈”等系统性术语。"
            "3. 不要主动提出“为您转接人工”或解释你在做什么。"
            "4. 如果不理解用户意思，直接反问“什么意思？”、“没看懂”等口语化表达。"
            "5. 语气要自然、简短，像朋友聊天一样。"
        )
    return ""

def enforce_qa_only(text, user_text):
    if not text:
        return text
    s = (text or "").strip()
    prefer_tc = False
    if re.search(r"[繁體臺灣幣裡裏於將這麼為麼後臺]", (user_text or "")):
        prefer_tc = True
    patterns_sc = [r"【答案-简体】(.*?)(?=\n|====|QA-|$)"]
    patterns_tc = [r"【答案-繁体】(.*?)(?=\n|====|QA-|$)"]
    patterns = (patterns_tc + patterns_sc) if prefer_tc else (patterns_sc + patterns_tc)
    picked = None
    for pat in patterns:
        m = re.search(pat, s, re.DOTALL)
        if m:
            picked = m.group(1).strip()
            break
    if picked is None:
        s = re.sub(r"(^|\n)\s*(Q[:：]|A[:：]).*", "", s)
        s = re.sub(r"(目录|页码|版权信息|API|索引|【问题[^】]*】|【答案[^】]*】|QA-[0-9]+|====)", "", s).strip()
        if not s:
            return ""
        picked = s
    picked = picked.split("\n")[0].strip()
    if _has_illegal_markers(picked):
        return ""
    if re.search(r"[\u4e00-\u9fff]", picked) and not re.search(r"[。！？!?]$", picked):
        picked = picked + "。"
    return picked

def _has_illegal_markers(s):
    if not s:
        return False
    markers = ["QA-", "【问题", "【答案", "===="]
    return any(m in s for m in markers)

def enforce_qa_only_single_line(text, user_text):
    if not text:
        return text
    s = text.strip()
    s = s.splitlines()[0] if "\n" in s else s
    s = s.split("====")[0]
    s = re.sub(r"(^|\n)\s*(Q[:：]|A[:：]).*", "", s)
    s = re.sub(r"(目录|页码|版权信息|API|索引|【问题[^】]*】|【答案[^】]*】|QA-[0-9]+)", "", s)
    s = s.strip()
    if not s:
        return ""
    if _has_illegal_markers(s):
        s = re.sub(r"(【问题[^】]*】|【答案[^】]*】|QA-[0-9]+|====)", "", s).strip()
    if re.search(r"[\u4e00-\u9fff]", s) and not re.search(r"[。！？!?]$", s):
        s = s + "。"
    return s

def _parse_qa_pairs_from_text(content):
    pairs = []
    if not content:
        return pairs
    lines = content.splitlines()
    pending_q = None
    answer_lines = []
    collecting = False
    for raw in lines:
        line = (raw or "").strip()
        if not line:
            if collecting and pending_q:
                answer_lines.append("")
            continue
        if line.lower().startswith("q:"):
            if pending_q and answer_lines:
                pairs.append((pending_q.strip(), "\n".join(answer_lines).strip()))
            pending_q = line[2:].strip()
            answer_lines = []
            collecting = False
            continue
        if line.lower().startswith("a:"):
            collecting = True
            answer_lines.append(line[2:].strip())
            continue
        if collecting and pending_q:
            answer_lines.append(line)
    if pending_q and answer_lines:
        pairs.append((pending_q.strip(), "\n".join(answer_lines).strip()))
    return pairs

def _parse_multi_lang_qa(content):
    blocks = []
    if not content:
        return blocks
    lines = content.splitlines()
    cur = {"q_sc":"", "q_tc":"", "a_sc":"", "a_tc":""}
    cur_key = None
    def flush():
        nonlocal cur
        if any(cur.values()):
            blocks.append({k: (v.strip()) for k, v in cur.items()})
        cur = {"q_sc":"", "q_tc":"", "a_sc":"", "a_tc":""}
    for raw in lines:
        line = (raw or "").strip()
        if not line:
            if cur_key:
                (cur[cur_key] if cur_key else "")
            continue
        if line.startswith("====="):
             continue
        if line.startswith("QA-"):
            flush()
            cur_key = None
            continue
        if line.startswith("【问题-简体】"):
            cur_key = "q_sc"
            cur[cur_key] += line.replace("【问题-简体】", "").strip()
            continue
        if line.startswith("【问题-繁体】"):
            cur_key = "q_tc"
            cur[cur_key] += line.replace("【问题-繁体】", "").strip()
            continue
        if line.startswith("【答案-简体】"):
            cur_key = "a_sc"
            cur[cur_key] += line.replace("【答案-简体】", "").strip()
            continue
        if line.startswith("【答案-繁体】"):
            cur_key = "a_tc"
            cur[cur_key] += line.replace("【答案-繁体】", "").strip()
            continue
        if cur_key:
            cur[cur_key] += ("\n" + line)
    flush()
    return [b for b in blocks if any(b.values())]

def _match_multi_lang_qa(blocks, user_msg):
    if not blocks or not user_msg:
        return None
    norm_msg = _normalize_text(user_msg)
    best = None
    best_score = -1.0
    for b in blocks:
        qsc = _normalize_text(b.get("q_sc",""))
        qtc = _normalize_text(b.get("q_tc",""))
        score_sc = difflib.SequenceMatcher(None, norm_msg, qsc).ratio() if qsc else -1.0
        score_tc = difflib.SequenceMatcher(None, norm_msg, qtc).ratio() if qtc else -1.0
        if score_sc > best_score:
            best_score = score_sc
            best = ("sc", b.get("a_sc",""))
        if score_tc > best_score:
            best_score = score_tc
            best = ("tc", b.get("a_tc",""))
    if best is None:
        return None
    return best

def _parse_markdown_kb(content):
    """
    通用 Markdown 分割器：按标题（#）分割知识库
    """
    lines = content.splitlines()
    blocks = []
    current_title = "General"
    current_content = []
    
    for line in lines:
        if line.strip().startswith('#'):
            if current_content:
                text = "\n".join(current_content).strip()
                if text:
                    blocks.append({"title": current_title, "content": text})
            current_title = line.strip().lstrip('#').strip()
            current_content = [line]
        else:
            current_content.append(line)
            
    if current_content:
        text = "\n".join(current_content).strip()
        if text:
            blocks.append({"title": current_title, "content": text})
            
    return blocks

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
        'CONV_ORCHESTRATION': False,
        'KB_ONLY_REPLY': False,
        'CONVERSATION_MODE': 'ai_visible'  # ai_visible / human_simulated
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
                    raw_value = line.split('=', 1)[1].strip()
                    
                    if key in ['PRIVATE_REPLY', 'GROUP_REPLY', 'GROUP_CONTEXT', 'AUDIT_ENABLED', 'AUTO_QUOTE', 'CONV_ORCHESTRATION', 'KB_ONLY_REPLY']:
                        config[key] = (value == 'on')
                    elif key == 'CONVERSATION_MODE':
                        if value in ['ai_visible', 'human_simulated']:
                            config[key] = value
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
                    elif key == 'AUDIT_MODE':
                        config[key] = value
                    elif key == 'AUDIT_SERVERS':
                        config[key] = raw_value
                    elif key == 'HANDOFF_KEYWORDS':
                        config[key] = raw_value
                    elif key == 'HANDOFF_MESSAGE':
                        config[key] = raw_value
                    elif key == 'KB_FALLBACK_MESSAGE':
                        config[key] = raw_value
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
    orch_enabled = bool(config.get('CONV_ORCHESTRATION', False))
    
    # 记录消息类型
    if event.is_private:
        stats['private_messages'] += 1
    elif event.is_group:
        stats['group_messages'] += 1

    if orch_enabled:
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

    def _handoff_intent_detect(user_msg):
        if not user_msg:
            return False
        s = (user_msg or "").strip().lower()
        keys_raw = str(config.get('HANDOFF_KEYWORDS', '') or '')
        keys = [k.strip().lower() for k in keys_raw.split(',') if k.strip()]
        if keys and any(k in s for k in keys):
            return True
        return False

    if _handoff_intent_detect(msg):
        reply = (config.get('HANDOFF_MESSAGE') or "").strip()
        if not reply:
            log_system("⚠️ HANDOFF_MESSAGE 未配置，已禁止默认兜底；跳过发送")
            return
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
            log_private(f"[trace:{trace_id}] HANDOFF_REPLY: {reply}")
        else:
            log_group(f"HANDOFF_REPLY: {reply}")
        stats['total_replies'] += 1
        stats['success_count'] += 1
        save_stats(stats)
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

        if config.get('KB_ONLY_REPLY', False):
            if _handoff_intent_detect(msg):
                conv_mode = config.get('CONVERSATION_MODE', 'ai_visible')
                reply = get_mode_specific_response(conv_mode, 'handoff')
                
                if not reply:
                    log_system("⚠️ HANDOFF_MESSAGE 未配置（KB_ONLY 分支），跳过发送")
                    return
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
                    log_private(f"[trace:{trace_id}] KB_ONLY_HANDOFF: {reply}")
                else:
                    log_group(f"KB_ONLY_HANDOFF: {reply}")
                stats['total_replies'] += 1
                stats['success_count'] += 1
                save_stats(stats)
                return
            log_system(f"[Trace] KB_ONLY Logic. Msg: {msg[:30]}...")
            kb_hits = retrieve_kb_context(msg, kb_items, topn=3)
            log_system(f"[Trace] KB Search Hits: {len(kb_hits)}")
            for i, hit in enumerate(kb_hits):
                log_system(f"  Hit {i}: {hit.get('title','')} (len={len(hit.get('content',''))})")

            reply = ""
            if kb_hits:
                # Concatenate contents
                context_text = "\n\n".join([f"--- Doc {i+1} ---\n{it.get('content','')}" for i, it in enumerate(kb_hits)])
                
                conv_mode = config.get('CONVERSATION_MODE', 'ai_visible')
                mode_guidance = build_conversation_mode_guidance(conv_mode)
                
                sys_prompt = (
                    "你是一个专业的客服助手。请根据以下知识库内容回答用户的问题。\n"
                    "如果知识库中包含答案，请直接回答，不要提及“根据知识库”或“文档”。\n"
                    "如果知识库中没有相关信息，请直接回复: NO_ANSWER_FOUND\n"
                    "请使用与用户提问相同的语言（简体或繁体）回答。\n"
                    f"{mode_guidance}\n"
                    f"\n【知识库内容】\n{context_text}"
                )
                
                log_system(f"[Trace] Calling LLM (Model: {AI_MODEL_NAME})...")
                
                # 🔁 自动重试逻辑 (处理 SSL 连接错误)
                for attempt in range(2):
                    try:
                        ai = get_ai_client()
                        resp = await ai.chat.completions.create(
                            model=AI_MODEL_NAME,
                            messages=[
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": msg}
                            ],
                            temperature=0.3
                        )
                        ans = resp.choices[0].message.content.strip()
                        log_system(f"[Trace] LLM Response: {ans[:50]}...")

                        if "NO_ANSWER_FOUND" not in ans:
                            reply = ans
                        else:
                            log_system("[Trace] LLM returned NO_ANSWER_FOUND")
                        
                        break # 成功则跳出循环

                    except APIConnectionError as e:
                        # 如果是连接错误，且当前启用了 SSL 验证，尝试关闭验证重试
                        if attempt == 0 and _ssl_verify_default():
                            log_system(f"⚠️ 连接失败: {e}。正在尝试关闭 SSL 验证并重试...")
                            os.environ["HTTPX_VERIFY_SSL"] = "false"
                            reset_ai_client()
                            continue
                        else:
                            log_system(f"⚠️ KB_ONLY LLM Error (Connection): {e}")
                            break
                    except Exception as e:
                        log_system(f"⚠️ KB_ONLY LLM Error: {e} (Type: {type(e)})")
                        break

            else:
                 log_system("[Trace] No KB hits found.")

            if not reply:
                log_system("[Trace] Using Fallback Message.")

            if not reply:
                reply = (config.get('KB_FALLBACK_MESSAGE') or "").strip()
                if not reply:
                    log_system("⚠️ KB_FALLBACK_MESSAGE 未配置（KB_ONLY RAG Miss），跳过发送")
                    return
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
                log_private(f"[trace:{trace_id}] KB_ONLY_REPLY: {reply}")
            else:
                log_group(f"KB_ONLY_REPLY: {reply}")
            stats['total_replies'] += 1
            stats['success_count'] += 1
            save_stats(stats)
            return
        
        # 编排模式专用变量
        orch_enabled = bool(config.get('CONV_ORCHESTRATION', False))
        model_override = AI_MODEL_NAME
        temp_override = config.get('AI_TEMPERATURE', 0.7)
        base_ai_client = get_ai_client()
        ai_client_orch = base_ai_client
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
                decision = await sup.decide(state, history, base_ai_client, AI_MODEL_NAME)
                
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
                    conv_mode = config.get('CONVERSATION_MODE', 'ai_visible')
                    handoff_msg = get_mode_specific_response(conv_mode, 'handoff')
                    await event.reply(handoff_msg)
                    return

                # --- 3. Stage Agent Execution ---
                # 4. KB_RETRIEVED (Stage Scope Filtering)
                current_stage = state.get("current_stage", "S0")
                # Filter KB items that have the current stage tag OR are global (no tags or 'all')
                filtered_kb = []
                for it in kb_items:
                    tags = it.get("tags") or []
                    # Allow Global (empty tags or 'all'/'global') OR specific stage match
                    if (not tags) or ("all" in tags) or ("global" in tags) or (current_stage in tags):
                        filtered_kb.append(it)
                
                kb_hits = retrieve_kb_context(msg, filtered_kb, topn=2)
                
                log_trace_event(trace_id, "KB_RETRIEVED", {
                    "stage_scope": [current_stage],
                    "hits": [{"kb_id": it.get("id"), "tags": it.get("tags")} for it in kb_hits]
                })
                qa_only_enabled, qa_reason = detect_qa_only(msg, kb_hits)
                if qa_only_enabled and kb_hits:
                    kb_hits = kb_hits[:1]
                    log_trace_event(trace_id, "QA_ONLY", {"enabled": True, "reason": qa_reason})

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
             kb_hits = retrieve_kb_context(msg, kb_items, topn=2)
             qa_only_enabled, qa_reason = detect_qa_only(msg, kb_hits)
             if qa_only_enabled and kb_hits:
                 kb_hits = kb_hits[:1]
                 log_trace_event(trace_id, "QA_ONLY", {"enabled": True, "reason": qa_reason})
                 if kb_hits:
                    parts = []
                    for it in kb_hits:
                        title = it.get("title","")
                        snippet = (it.get("content","") or "")
                        if len(snippet) > 800: snippet = snippet[:800]
                        parts.append(f"[{title}]\n{snippet}")
                    kb_context = "\n\n".join(parts)
                    system_with_kb = system_prompt + "\n\n【知识库参考】\n" + kb_context

        messages = [{"role": "system", "content": system_with_kb}]
        
        # Inject Conversation Mode Guidance
        conv_mode = config.get('CONVERSATION_MODE', 'ai_visible')
        conv_guidance = build_conversation_mode_guidance(conv_mode)
        if conv_guidance:
             messages.append({"role": "system", "content": conv_guidance})

        if 'qa_only_enabled' in locals() and qa_only_enabled:
            messages.append({"role": "system", "content": build_qa_only_guidance()})
        messages = messages + history + [{"role": "user", "content": msg}]

        try:
            if event.is_private:
                log_private(f"[trace:{trace_id}] 🤖 AI 正在思考...")
            else:
                log_group("🤖 AI 正在思考...")
            
            # 🔁 自动重试逻辑 (处理 SSL 连接错误)
            gen_result = None
            for attempt in range(2):
                try:
                    # 重新获取 client (确保重试时使用新配置)
                    # 注意：如果原本是编排模式且使用了自定义 URL，这里会回退到默认 AI_BASE_URL，
                    # 但作为连接失败的兜底，这是可以接受的。
                    current_client = get_ai_client() if attempt > 0 else ai_client_orch
                    
                    audit_manager = AuditManager(current_client, model_override, load_config, platform="telegram")
                    
                    # 6. STYLE_GUARD / AUDIT (Implied)
                    gen_result = await audit_manager.generate_with_audit(
                        messages=messages,
                        user_input=msg,
                        history=history,
                        temperature=temp_override
                    )
                    break # Success
                except APIConnectionError as e:
                    if attempt == 0 and _ssl_verify_default():
                        log_system(f"⚠️ [常规回复] 连接失败: {e}。正在尝试关闭 SSL 验证并重试...")
                        os.environ["HTTPX_VERIFY_SSL"] = "false"
                        reset_ai_client()
                        continue
                    else:
                        raise e 
                except Exception:
                    raise
            
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
                    stage=current_stage,
                    user_content=msg,
                    bot_response=reply
                )
            except Exception as e:
                log_system(f"⚠️ Failed to record message event: {e}")

            if 'qa_only_enabled' in locals() and qa_only_enabled:
                reply = enforce_qa_only(reply, msg)
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
    if _ssl_verify_default():
         log_system("⚠️ [配置警告] SSL验证已开启 (HTTPX_VERIFY_SSL != false)。")
         log_system("   如果遇到连接错误，请在 .env 中设置: HTTPX_VERIFY_SSL=false")
    client.start()
    client.run_until_disconnected()
