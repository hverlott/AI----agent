import os
import shutil
import sys
from dotenv import load_dotenv

def setup_env():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(base_dir, '.env')
    env_example_path = os.path.join(base_dir, '.env.example')
    
    if not os.path.exists(env_path) and os.path.exists(env_example_path):
        try:
            shutil.copy(env_example_path, env_path)
            print(f"⚠️ 检测到 .env 缺失，已根据 .env.example 自动生成: {env_path}")
        except Exception as e:
            print(f"❌ 无法自动生成 .env: {e}")

    load_dotenv(env_path)

    if not os.getenv('TELEGRAM_API_ID'):
        print("================================================================")
        print("❌ 错误: 未检测到 TELEGRAM_API_ID")
        print("⚠️ 请打开 .env 文件，填写您的 Telegram API 配置和 AI 密钥")
        print("================================================================")
        sys.exit(1)
    
    # Win32 Console Fix
    if sys.platform == 'win32':
        try:
            import codecs
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
