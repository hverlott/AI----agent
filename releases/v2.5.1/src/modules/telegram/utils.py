import json
import os
import hashlib
import base64
from datetime import datetime, timedelta

from telethon import TelegramClient

async def get_session_user(session_path, api_id, api_hash):
    """
    尝试从 Session 文件中读取当前用户信息 (username/phone/name)
    """
    if not api_id or not api_hash:
        return None
    
    client = None
    try:
        # Telethon session 参数如果是路径，会自动识别
        client = TelegramClient(session_path, int(api_id), api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return None
            
        me = await client.get_me()
        await client.disconnect()
        
        if me.username:
            return me.username
        if me.phone:
            return me.phone
        
        name = f"{me.first_name or ''} {me.last_name or ''}".strip()
        return name if name else str(me.id)
            
    except Exception as e:
        print(f"Error reading session {session_path}: {e}")
        if client:
            try:
                await client.disconnect()
            except:
                pass
        return None

from src.modules.telegram.whitelist_manager import WhitelistManager

async def record_group(event, config_manager, logger):
    if not event.is_group:
        return
    chat_id = getattr(event, 'chat_id', None)
    if chat_id is None:
        return
    chat_id_str = str(chat_id)
    
    # Use project-level cache path logic matching admin_multi.py
    # /cache/group_whitelist/{tenant_id}_group_cache.json
    tenant_id = getattr(config_manager, 'tenant_id', 'default')
    
    # Resolve project root from this file location
    # d:\SaaS-AIs\releases\v2.5.1\src\modules\telegram\utils.py
    # -> src -> modules -> telegram -> utils.py (Go up 4 levels to root)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cache_dir = os.path.join(project_root, "cache", "group_whitelist")
    cache_file = os.path.join(cache_dir, f"{tenant_id}_group_cache.json")
    
    cache = {}
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
    except:
        pass

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
    # Add username if available
    # entry['username'] = ... (optional)
    
    cache[chat_id_str] = entry
    
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        descriptor = title or str(chat_id)
        # Log less frequently to avoid spam, or only on new entry?
        # logger.log_system(f"🗂️ 缓存群聊: {descriptor} ({chat_id})")
    except Exception as e:
        logger.log_system(f"⚠️ 保存群组缓存失败: {e}")

def load_selected_group_ids(config_manager):
    try:
        tenant_id = getattr(config_manager, 'tenant_id', 'default')
        wm = WhitelistManager(tenant_id)
        raw_ids = wm.get_whitelist_ids()
        selected = set()
        for gid in raw_ids:
            try:
                selected.add(int(str(gid).strip()))
            except Exception:
                pass
        return selected
    except Exception as e:
        print(f"Error loading whitelist via manager: {e}")
        return set()

async def get_chat_history(client, chat_id, limit=8, max_id=0):
    messages = []
    try:
        async for msg in client.iter_messages(chat_id, limit=limit, max_id=max_id):
            if msg.text:
                role = "assistant" if msg.out else "user"
                messages.append({"role": role, "content": msg.text})
        return messages[::-1]
    except Exception:
        return []

async def get_prev_incoming_message(client, chat_id, max_id=0):
    try:
        async for msg in client.iter_messages(chat_id, limit=1, max_id=max_id):
            if msg and msg.text and not msg.out:
                return msg
    except Exception:
        return None
    return None

def ensure_session_meta(session_path, meta_path, user_id, username, validity_days=30, salt=""):
    token = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")
    token_hash = hashlib.sha256((token + salt).encode("utf-8")).hexdigest()
    meta = {
        "token_hash": token_hash,
        "session_file": os.path.basename(session_path),
        "user_id": str(user_id),
        "username": username or "",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=validity_days)).isoformat()
    }
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta

async def check_session_validity(session_path, api_id, api_hash, meta_path, renew_threshold_days=3, renew_days=30):
    result = {
        "meta_exists": False,
        "authorized": False,
        "expires_at": None,
        "expired": None,
        "username": None
    }
    meta = None
    if os.path.exists(meta_path):
        result["meta_exists"] = True
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                result["expires_at"] = meta.get("expires_at")
        except Exception:
            meta = None
    client = None
    try:
        client = TelegramClient(session_path, int(api_id), api_hash)
        await client.connect()
        if await client.is_user_authorized():
            result["authorized"] = True
            me = await client.get_me()
            result["username"] = me.username or (me.phone or str(me.id))
        await client.disconnect()
    except Exception:
        if client:
            try:
                await client.disconnect()
            except:
                pass
    if meta and result["expires_at"]:
        try:
            exp = datetime.fromisoformat(result["expires_at"])
            now = datetime.now()
            result["expired"] = now >= exp
            remain = (exp - now).days
            if result["authorized"] and remain <= renew_threshold_days:
                meta["expires_at"] = (now + timedelta(days=renew_days)).isoformat()
                try:
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
        except Exception:
            result["expired"] = None
    return result
