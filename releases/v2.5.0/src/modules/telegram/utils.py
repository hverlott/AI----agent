import json
import os
from datetime import datetime

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

async def record_group(event, config_manager, logger):
    if not event.is_group:
        return
    chat_id = getattr(event, 'chat_id', None)
    if chat_id is None:
        return
    chat_id_str = str(chat_id)
    
    cache_file = config_manager.get_platform_path("group_cache.json")
    cache = {}
    try:
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
    cache[chat_id_str] = entry
    
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        descriptor = title or str(chat_id)
        logger.log_system(f"🗂️ 缓存群聊: {descriptor} ({chat_id})")
    except Exception as e:
        logger.log_system(f"⚠️ 保存群组缓存失败: {e}")

def load_selected_group_ids(config_manager):
    file_path = config_manager.get_platform_path("selected_groups.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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
