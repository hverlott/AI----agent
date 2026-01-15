import os
import sys
import argparse
import asyncio
from src.config.env_setup import setup_env
from src.modules.telegram.bot import TelegramBotApp

# 1. Setup Environment
setup_env()

# 2. Parse Arguments
parser = argparse.ArgumentParser(description='Telegram AI Bot (Modular v2.5.0)')
parser.add_argument('--tenant', type=str, default='default', help='Tenant ID')
parser.add_argument('--session', type=str, default='userbot_session', help='Session file name (without .session)')
args, unknown = parser.parse_known_args()

# 3. Load Credentials (Priority: Tenant Config > Env Vars)
import json

# Default from Environment
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
AI_KEY = os.getenv('AI_API_KEY')
AI_URL = os.getenv('AI_BASE_URL')
AI_MODEL = os.getenv('AI_MODEL_NAME')

# Try to load from Tenant Config
tenant_config_path = os.path.join("data", "tenants", args.tenant, "platforms", "telegram", "config.json")
if os.path.exists(tenant_config_path):
    try:
        with open(tenant_config_path, 'r', encoding='utf-8') as f:
            t_cfg = json.load(f)
            # Override if present in tenant config
            if t_cfg.get("api_id"): API_ID = t_cfg["api_id"]
            if t_cfg.get("api_hash"): API_HASH = t_cfg["api_hash"]
            if t_cfg.get("ai_api_key"): AI_KEY = t_cfg["ai_api_key"]
            if t_cfg.get("ai_base_url"): AI_URL = t_cfg["ai_base_url"]
            if t_cfg.get("ai_model_name"): AI_MODEL = t_cfg["ai_model_name"]
            print(f"✅ Loaded API credentials from tenant config: {tenant_config_path}")
    except Exception as e:
        print(f"⚠️ Failed to load tenant config: {e}")

# Validation
if not API_ID or not API_HASH:
    print("❌ Error: Missing TELEGRAM_API_ID or TELEGRAM_API_HASH")
    print("👉 Please configure API credentials in the Admin Panel or .env file")
    sys.exit(1)

if __name__ == '__main__':
    # 4. Initialize and Run Bot
    try:
        bot = TelegramBotApp(
            tenant_id=args.tenant,
            session_name=args.session,
            api_id=API_ID,
            api_hash=API_HASH,
            ai_api_key=AI_KEY,
            ai_base_url=AI_URL,
            ai_model_name=AI_MODEL
        )
        
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        import traceback
        traceback.print_exc()
