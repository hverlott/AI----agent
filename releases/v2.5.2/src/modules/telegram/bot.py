import asyncio
import os
from telethon import TelegramClient
from src.config.loader import ConfigManager
from src.core.logger import TenantLogger
from src.core.database import db
from src.core.ai import AIClientManager
from src.modules.knowledge_base.engine import KBEngine
from src.modules.knowledge_base.loader import KBLoader
# handlers 将在之后导入以避免循环引用，或者使用方法注册

class TelegramBotApp:
    def __init__(self, tenant_id, session_name, api_id, api_hash, ai_api_key, ai_base_url, ai_model_name):
        self.tenant_id = tenant_id
        self.cfg = ConfigManager(tenant_id)
        self.logger = TenantLogger(self.cfg.get_platform_path("logs"))
        self.db = db
        
        self.ai_model_name = ai_model_name
        self.ai_manager = AIClientManager(ai_api_key, ai_base_url, self.logger)
        
        # Load RAG config
        rag_conf = self.cfg.load_rag_config()
        embedding_model = rag_conf.get("embedding_model_id", "text-embedding-3-small")
        
        # Initialize KBEngine with sync client and model
        self.kb_engine = KBEngine(
            client=self.ai_manager.get_sync_client(), 
            embedding_model=embedding_model
        )
        self.kb_loader = KBLoader(self.cfg, self.logger, self.db)
        
        # Initialize AuditManager with tenant log path
        from src.modules.audit.manager import AuditManager
        # We need to defer import or handle it carefully, but AuditManager is already imported in some places?
        # Actually AuditManager is not imported at top level here.
        # But wait, where is AuditManager used? It seems it's used inside handlers? 
        # Or is it initialized here? 
        # Checking imports... it is NOT imported at top level.
        
        # NOTE: In v2.5.1, AuditManager might be initialized inside handlers or lazily. 
        # But if we want to pass log_dir, we should probably initialize it here or ensure handlers get it.
        # Let's check where AuditManager is used. 
        # Based on previous reads, it seems AuditManager is used in `handlers.py` or similar.
        # I will check `handlers.py` next. For now, I'll assume I need to pass it if I initialize it.
        
        session_path = self.cfg.get_session_path(session_name)
        self.client = TelegramClient(session_path, int(api_id), api_hash)
        
        # Stats management
        self.stats = self._load_stats()
        
    def _load_stats(self):
        # 简单实现，实际可以复用 main.py 逻辑并移入 utils
        stats_file = self.cfg.get_platform_path("stats.json")
        default_stats = {
            "total_messages": 0, "total_replies": 0, "private_messages": 0,
            "group_messages": 0, "success_count": 0, "error_count": 0,
            "start_time": None, "last_active": None
        }
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                import json
                stats = json.load(f)
                return stats
        except:
            return default_stats

    def save_stats(self):
        import json
        from datetime import datetime
        stats_file = self.cfg.get_platform_path("stats.json")
        try:
            self.stats['last_active'] = datetime.now().isoformat()
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.log_system(f"⚠️ 保存统计失败: {e}")

    async def run(self):
        from src.modules.telegram.handlers import register_handlers
        register_handlers(self)
        
        # Load keywords once
        self.keywords = self.cfg.load_keywords()
        self.logger.log_system(f"✅ 已加载关键词配置: {len(self.keywords)} 个")
        
        self.logger.log_system("🚀 Telegram Bot 启动中...")
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                conf = self.cfg.load_config()
                token = conf.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
                if token:
                    await self.client.start(bot_token=token)
                else:
                    self.logger.log_system("❌ 未授权会话，且未配置 TELEGRAM_BOT_TOKEN。请在后台完成手机号登录或设置环境变量 TELEGRAM_BOT_TOKEN。")
                    return
        except Exception as e:
            self.logger.log_system(f"❌ 连接 Telegram 失败: {e}")
            return
        
        # Sync groups on startup
        try:
            await self._sync_groups()
        except Exception as e:
            self.logger.log_system(f"⚠️ 启动时同步群组失败: {e}")
            
        await self.client.run_until_disconnected()

    async def _sync_groups(self):
        """Sync all groups to cache on startup"""
        try:
            dialogs = await self.client.get_dialogs()
            groups = {}
            import json
            from datetime import datetime
            
            now_iso = datetime.now().isoformat()
            
            for d in dialogs:
                if d.is_group or d.is_channel:
                    groups[str(d.id)] = {
                        "id": d.id,
                        "title": d.title,
                        "type": "channel" if d.is_channel else "group",
                        "username": getattr(d.entity, 'username', None),
                        "last_seen": now_iso
                    }
            
            # Construct path relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            cache_dir = os.path.join(project_root, "cache", "group_whitelist")
            os.makedirs(cache_dir, exist_ok=True)
            
            cache_file = os.path.join(cache_dir, f"{self.tenant_id}_group_cache.json")
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(groups, f, ensure_ascii=False, indent=2)
                
            self.logger.log_system(f"✅ 群组缓存同步完成: {len(groups)} 个群组")
            
        except Exception as e:
            self.logger.log_system(f"❌ 群组同步错误: {e}")
            raise e
