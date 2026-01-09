import logging
import json
import os
import httpx
import random
import hashlib
from auditor import Auditor, AuditResult
from keyword_manager import KeywordManager

# 配置日志
log_dir = os.path.join("platforms", "telegram", "logs")
os.makedirs(log_dir, exist_ok=True)

# 使用独立的 Logger，确保日志一定会写入文件，避免被其他模块配置覆盖
logger = logging.getLogger('AuditManager')
logger.setLevel(logging.INFO)
# 清除可能存在的旧 handlers，防止重复写入
if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler(os.path.join(log_dir, 'audit.log'), encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class FallbackCache:
    def __init__(self, path):
        self.path = path
        self._mtime = None
        self._messages = ["系统繁忙，请稍后再试"]
        self._load()
    def _load(self):
        try:
            mtime = os.path.getmtime(self.path)
            if self._mtime != mtime:
                msgs = []
                with open(self.path, 'r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if s and not s.startswith('#'):
                            msgs.append(s)
                if msgs:
                    self._messages = msgs
                self._mtime = mtime
        except Exception:
            pass
    def get_message(self):
        self._load()
        return random.choice(self._messages)

class RemoteAuditor:
    def __init__(self, server_urls):
        self.server_urls = [url.strip() for url in server_urls.split(',') if url.strip()]
        self.client = httpx.AsyncClient(timeout=3.0, verify=False)
        self.last_ok_url = None
    
    async def audit_content(self, user_input, draft_reply, history) -> AuditResult:
        payload = {
            "user_input": user_input,
            "draft_reply": draft_reply,
            "history": history
        }
        
        last_error = None
        ordered = []
        if self.last_ok_url:
            ordered.append(self.last_ok_url)
        ordered.extend([u for u in self.server_urls if u != self.last_ok_url])
        for url in ordered:
            try:
                # 确保 URL 格式正确
                if not url.startswith("http"):
                    url = f"http://{url}"
                audit_url = f"{url.rstrip('/')}/audit"
                
                logger.info(f"Trying audit server: {audit_url}")
                response = await self.client.post(audit_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # 兼容新旧格式
                status = data.get('status', '')
                if not status and 'approved' in data:
                    status = "PASS" if data['approved'] else "FAIL"
                
                self.last_ok_url = url
                return AuditResult(status, data.get('reason', ''), data.get('suggestion', ''))
            except Exception as e:
                logger.warning(f"Audit failed at {url}: {e}")
                last_error = e
                continue
        
        # 所有服务器都失败
        logger.error(f"All audit servers failed. Last error: {last_error}")
        # 降级策略：返回 FAIL (System Error)，触发兜底
        return AuditResult("FAIL", "System Error (Fail-Closed)", "Audit system unavailable")

class AuditManager:
    def __init__(self, ai_client, model_name, config_loader=None):
        self.ai_client = ai_client
        self.model_name = model_name
        self.config_loader = config_loader
        self.keyword_manager = KeywordManager()
        self._fallback_cache = FallbackCache(os.path.join("platforms", "telegram", "audit_fallback.txt"))
        
        # 根据配置决定使用本地还是远程审核
        mode = self._get_config('AUDIT_MODE', 'local').lower()
        if mode == 'remote':
            servers = self._get_config('AUDIT_SERVERS', 'http://127.0.0.1:8000')
            self.auditor = RemoteAuditor(servers)
            logger.info(f"Initialized RemoteAuditor with servers: {servers}")
        else:
            self.auditor = Auditor() # 本地模式
            logger.info("Initialized LocalAuditor")
    
    def _get_config(self, key, default):
        if self.config_loader:
            return self.config_loader().get(key, default)
        return default
    def _get_bool(self, key, default=False):
        val = self._get_config(key, default)
        return str(val).lower() in ('true', 'on', '1', 'yes')
    def _get_int(self, key, default=0):
        try:
            return int(self._get_config(key, default))
        except Exception:
            return default
    def _get_float(self, key, default=0.0):
        try:
            return float(self._get_config(key, default))
        except Exception:
            return default

    async def generate_with_audit(self, messages, user_input, history, temperature=0.7):
        """
        带审核的生成流程：
        生成 -> 审核 -> (不通过 -> 重试) * N -> 兜底话术
        """
        # 读取配置
        enabled = self._get_bool('AUDIT_ENABLED', False)
        
        # 严格限制重试次数为 2 (总尝试 3 次)
        max_retries = 2
        
        if not enabled:
            # 如果审核关闭，直接生成
            logger.info("Audit disabled, generating directly.")
            response = await self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=500
            )
            return response.choices[0].message.content

        # 初始上下文
        current_messages = messages.copy()
        retry_count = 0
        
        # 前置检查：用户输入关键词
        safe_input, cat_in, word_in = self.keyword_manager.check_text(user_input or "")
        if not safe_input:
            logger.warning(f"Input keyword check failed: '{word_in}' in '{cat_in}'")
            return self._get_fallback_message()
        
        while retry_count <= max_retries:
            # 1. 生成回复
            logger.info(f"Generating reply (Attempt {retry_count + 1}/{max_retries + 1})...")
            try:
                strength = self._get_float('AUDIT_GUIDE_STRENGTH', 0.7)
                if strength >= 0.7:
                    guide_text = "仅回答用户当前问题；避免提供具体方案或营销语；严格控制在200字内；保持中立与专业语气。"
                else:
                    guide_text = "优先直接回答当前问题；避免营销语或具体方案；建议控制在200字内；保持中立与专业语气。"
                guidance_msg = {
                    "role": "system",
                    "content": guide_text
                }
                messages_injected = [guidance_msg] + current_messages
                response = await self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages_injected,
                    temperature=temperature,
                    max_tokens=500
                )
                draft_reply = response.choices[0].message.content
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                # 生成失败直接兜底
                return self._get_fallback_message()

            # 1.5 关键词检测
            is_safe, category, word = self.keyword_manager.check_text(draft_reply)
            if not is_safe:
                logger.warning(f"Keyword check failed: Found '{word}' in category '{category}'")
                audit_result = AuditResult("FAIL", f"Contains forbidden keyword: {word}", "Remove sensitive content")
            else:
                # 2. 审核回复 (LLM)
                logger.info(f"Auditing draft: {draft_reply[:30]}...")
                audit_result = await self.auditor.audit_content(user_input, draft_reply, history)
            
            # 记录详细日志
            log_entry = {
                "timestamp": str(logging.Formatter.converter), 
                "retry": retry_count,
                "status": audit_result.status,
                "approved": audit_result.approved,
                "reason": audit_result.reason,
                "suggestion": audit_result.suggestion
            }
            logger.info(f"Audit Result: {json.dumps(log_entry, default=str, ensure_ascii=False)}")

            # 3. 严格校验 PASS
            if audit_result.approved:
                # 只有明确 PASS 才通过
                return draft_reply
            
            # 4. 如果不通过，准备重试
            retry_count += 1
            if retry_count > max_retries:
                logger.warning("Max retries reached. Triggering fallback.")
                return self._get_fallback_message()

            # 5. 清空上下文缓存确保独立判定
            # 重置 current_messages 为原始 messages，不携带上次失败的上下文
            # 这样每次生成都是独立的（依赖 temperature 产生变化）
            current_messages = messages.copy()
            logger.info("Context cleared for retry.")

        return self._get_fallback_message()

    def _get_fallback_message(self):
        msg = self._fallback_cache.get_message()
        msg_hash = hashlib.md5(msg.encode('utf-8')).hexdigest()
        logger.info(f"Selected fallback message hash: {msg_hash}")
        return msg
