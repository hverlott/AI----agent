import os
import json

class ConfigManager:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        # Define base paths
        data_dir = os.environ.get("SAAS_DATA_DIR", "data")
        self.base_dir = os.path.join(data_dir, "tenants", self.tenant_id)
        self.platform_dir = os.path.join(self.base_dir, "platforms", "telegram")
        self.sessions_dir = os.path.join(self.base_dir, "sessions")
        
        # Ensure directories exist
        os.makedirs(self.platform_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)

    def get_platform_path(self, filename):
        return os.path.join(self.platform_dir, filename)

    def get_session_path(self, session_name):
        name = session_name
        if name.endswith('.session'):
            name = name[:-8]
        return os.path.join(self.sessions_dir, name)

    def load_system_prompt(self):
        prompt_file = self.get_platform_path("prompt.txt")
        default_prompt = "你是一个幽默、专业的个人助理，帮机主回复消息。请用自然、友好的语气回复。"
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content if content else default_prompt
        except Exception:
            return default_prompt

    def load_keywords(self):
        keywords_file = self.get_platform_path("keywords.txt")
        keywords = []
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    keyword = line.strip()
                    if keyword and not keyword.startswith('#'):
                        keywords.append(keyword)
            return keywords
        except Exception:
            return []

    def load_config(self):
        config_file = self.get_platform_path("config.txt")
        config = {
            'PRIVATE_REPLY': True,
            'GROUP_REPLY': True,
            'GROUP_CONTEXT': False,
            'AI_TEMPERATURE': 0.7,
            'AUDIT_ENABLED': True,
            'AUDIT_MAX_RETRIES': 3,
            'AUDIT_TEMPERATURE': 0.0,
            'REPLY_DELAY_MIN_SECONDS': 3.0,
            'REPLY_DELAY_MAX_SECONDS': 10.0,
            'AUTO_QUOTE': False,
            'QUOTE_INTERVAL_SECONDS': 30.0,
            'QUOTE_MAX_LEN': 200,
            'CONV_ORCHESTRATION': False,
            'KB_ONLY_REPLY': False,
            'CONVERSATION_MODE': 'ai_visible'
        }
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, raw_value = line.split('=', 1)
                        key = key.strip()
                        raw_value = raw_value.strip()
                        value_lower = raw_value.lower()
                        
                        if key in ['PRIVATE_REPLY', 'GROUP_REPLY', 'GROUP_CONTEXT', 'AUDIT_ENABLED', 'AUTO_QUOTE', 'CONV_ORCHESTRATION', 'KB_ONLY_REPLY']:
                            config[key] = (value_lower == 'on')
                        elif key == 'CONVERSATION_MODE':
                            if value_lower in ['ai_visible', 'human_simulated']:
                                config[key] = value_lower
                        elif key in ['AI_TEMPERATURE', 'AUDIT_TEMPERATURE', 'REPLY_DELAY_MIN_SECONDS', 'REPLY_DELAY_MAX_SECONDS', 'QUOTE_INTERVAL_SECONDS']:
                            try:
                                config[key] = float(value_lower)
                            except ValueError:
                                pass
                        elif key in ['AUDIT_MAX_RETRIES', 'QUOTE_MAX_LEN']:
                            try:
                                config[key] = int(value_lower)
                            except ValueError:
                                pass
                        else:
                            # String values (AUDIT_MODE, AUDIT_SERVERS, HANDOFF_KEYWORDS, etc.)
                            config[key] = raw_value
            return config
        except Exception:
            return config

    def set_kb_refresh_off(self):
        try:
            path = self.get_platform_path("config.txt")
            if not os.path.exists(path): return
            with open(path, "r", encoding="utf-8") as f: lines = f.readlines()
            with open(path, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.strip().startswith("KB_REFRESH="):
                        f.write("KB_REFRESH=off\n")
                    else:
                        f.write(line)
        except Exception:
            pass

    def load_ai_providers(self):
        """Load the ai_providers.json configuration."""
        path = os.path.join(self.base_dir, "ai_providers.json")
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f).get("providers", [])
        except Exception:
            pass
        return []

    def get_model_config(self, model_identifier):
        """
        Find configuration for a specific model identifier.
        Identifier format: "provider:model" or just "provider" (if model is implicit)
        """
        providers = self.load_ai_providers()
        if not providers:
            return None
            
        # Try exact match first (if identifier has provider:model format)
        if ":" in model_identifier:
            prov_name, model_name = model_identifier.split(":", 1)
            for p in providers:
                if p.get("provider") == prov_name and p.get("model") == model_name:
                    return p
        
        # Try finding by provider name only or model name only as fallback
        for p in providers:
            # Check if identifier matches provider name
            if p.get("provider") == model_identifier:
                return p
            # Check if identifier matches model name
            if p.get("model") == model_identifier:
                return p
                
        return None
