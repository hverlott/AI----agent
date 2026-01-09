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

# 3. Load Env Vars
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
AI_KEY = os.getenv('AI_API_KEY')
AI_URL = os.getenv('AI_BASE_URL')
AI_MODEL = os.getenv('AI_MODEL_NAME')

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
