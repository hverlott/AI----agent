import os
import httpx
from openai import AsyncOpenAI

class AIClientManager:
    def __init__(self, api_key, base_url, logger):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logger
        self.http_client = None
        self.ai_client = None
        
        # 自动修复 Base URL
        if self.base_url:
            if not self.base_url.startswith("http"):
                self.base_url = f"https://{self.base_url}"
            if "://55.ai" in self.base_url:
                self.base_url = self.base_url.replace("://55.ai", "://api.55.ai")
                self.logger.log_system("⚠️ 检测到旧域名，已自动修正为 api.55.ai")
            if "/chat/completions" in self.base_url:
                self.base_url = self.base_url.replace("/chat/completions", "")
            if not self.base_url.endswith("/v1"):
                self.base_url = self.base_url.rstrip("/") + "/v1"
            self.logger.log_system(f"🔧 AI 接口地址已修正为: {self.base_url}")

    def _ssl_verify_default(self):
        v = (os.getenv("HTTPX_VERIFY_SSL") or "").strip().lower()
        if v in ("0", "false", "no"):
            return False
        return True

    def get_client(self):
        if self.ai_client is None or self.http_client is None:
            ssl_mode = self._ssl_verify_default()
            self.logger.log_system(f"🔌 初始化 AI 客户端: SSL验证={ssl_mode}")
            self.http_client = httpx.AsyncClient(verify=ssl_mode, timeout=30.0)
            self.ai_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=self.http_client
            )
        return self.ai_client

    def reset_client(self):
        self.http_client = None
        self.ai_client = None
        self.logger.log_system("🔄 AI 客户端已重置 (准备重新初始化)")

def create_client_from_config(model_config, verify_ssl=True):
    """
    Create an AsyncOpenAI client from a model configuration dict.
    config: { "provider": "...", "base_url": "...", "api_key": "...", "model": "..." }
    """
    if not model_config:
        return None
        
    api_key = model_config.get("api_key")
    base_url = model_config.get("base_url")
    
    # Auto-fix URL logic
    if base_url:
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        if "://55.ai" in base_url:
            base_url = base_url.replace("://55.ai", "://api.55.ai")
        if "/chat/completions" in base_url:
            base_url = base_url.replace("/chat/completions", "")
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
            
    try:
        timeout = float(model_config.get("timeout", 30.0))
    except:
        timeout = 30.0

    http_client = httpx.AsyncClient(verify=verify_ssl, timeout=timeout)
    
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=http_client
    )
