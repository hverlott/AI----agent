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
        
        self.kb_engine = KBEngine()
        self.kb_loader = KBLoader(self.cfg, self.logger, self.db)
        
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
        
        self.logger.log_system("🚀 Telegram Bot 启动中...")
        await self.client.start()
        await self.client.run_until_disconnected()
