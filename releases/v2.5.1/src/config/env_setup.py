import os
import shutil
import sys
from dotenv import load_dotenv

def setup_env():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(base_dir, '.env')
    
    # Check parent/parent if not found (for versioned structure)
    if not os.path.exists(env_path):
        root_env = os.path.abspath(os.path.join(base_dir, "..", "..", ".env"))
        if os.path.exists(root_env):
             env_path = root_env

    env_example_path = os.path.join(base_dir, '.env.example')
    
    if not os.path.exists(env_path) and os.path.exists(env_example_path):
        try:
            shutil.copy(env_example_path, env_path)
            print(f"⚠️ 检测到 .env 缺失，已根据 .env.example 自动生成: {env_path}")
        except Exception as e:
            print(f"❌ 无法自动生成 .env: {e}")

    load_dotenv(env_path)

    if not os.getenv('TELEGRAM_API_ID'):
        # v2.5.1: 在 SaaS 模式下，允许环境变量为空，转而使用租户级配置
        # 仅在非 SaaS 模式（如旧版单机）或确实需要时才警告
        pass
        # print("================================================================")
        # print("⚠️ 提示: 未检测到系统级 TELEGRAM_API_ID (SaaS 模式下请在后台配置租户密钥)")
        # print("================================================================")
    
    # Win32 Console Fix
    if sys.platform == 'win32':
        try:
            import codecs
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8') # type: ignore
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8') # type: ignore
        except:
            pass
