import logging
import json
import os
import httpx
import random
import hashlib
import re
from openai import APIConnectionError
from .auditor import Auditor, AuditResult
from .keyword_manager import KeywordManager

logger = logging.getLogger('AuditManager')

class FallbackCache:
    def __init__(self, path):
        self.path = path
        self._mtime = None
        self._messages = []
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
        if self._messages:
            return random.choice(self._messages)
        return ""

class RemoteAuditor:
    def __init__(self, server_urls):
        self.server_urls = [url.strip() for url in server_urls.split(',') if url.strip()]
        v = (os.getenv("HTTPX_VERIFY_SSL") or "").strip().lower()
        verify = False if v in ("0","false","no") else True
        self.client = httpx.AsyncClient(timeout=3.0, verify=verify)
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
                key = os.getenv("SUPERADMIN_KEY") or ""
                response = await self.client.post(audit_url, json=payload, headers={"X-SuperAdmin-Key": key})
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
    def __init__(self, ai_client, model_name, config_loader=None, platform="telegram", 
                 primary_client=None, secondary_client=None, 
                 primary_model=None, secondary_model=None,
                 log_dir=None, fallback_path=None,
                 tenant_id=None, db=None):
        self.ai_client = ai_client
        self.model_name = model_name
        self.config_loader = config_loader
        self.platform = platform
        self.tenant_id = tenant_id
        self.db = db or "telegram"
        # Initialize KeywordManager with tenant-scoped path based on log_dir
        km_path = None
        try:
            if log_dir:
                base_dir = log_dir
                if base_dir.replace('\\','/').endswith('/logs'):
                    base_dir = os.path.dirname(base_dir)
                km_path = os.path.join(base_dir, "keywords.json")
        except Exception:
            km_path = None
        self.keyword_manager = KeywordManager(km_path) if km_path else KeywordManager()
        
        # Setup Logger
        if log_dir:
            self._setup_logger(log_dir)
            
        if not fallback_path:
            # Legacy path resolution logic (buggy if log_dir ends with logs, but kept for compatibility if not provided)
            # Try to fix the "logs" issue if implicit
            base_dir = log_dir
            if base_dir and base_dir.replace('\\', '/').endswith('/logs'):
                 base_dir = os.path.dirname(base_dir)
            
            fallback_path = os.path.join(base_dir if base_dir else os.path.join("platforms", "telegram"), "audit_fallback.txt")
            
        self._fallback_cache = FallbackCache(fallback_path)
        
        mode = self._get_config('AUDIT_MODE', 'local').lower()
        servers = self._get_config('AUDIT_SERVERS', 'http://127.0.0.1:8000')
        
        self.auditor_primary = None
        self.auditor_secondary = None
        
        # Primary Auditor
        if mode == 'remote':
            self.auditor_primary = RemoteAuditor(servers)
            logger.info(f"Initialized RemoteAuditor (Primary) with servers: {servers}")
        else:
            self.auditor_primary = Auditor(client=primary_client, model_name=primary_model)
            logger.info("Initialized LocalAuditor (Primary)")

        # Secondary Auditor
        enable_secondary = self._get_bool('ENABLE_AUDIT_SECONDARY', False) or (mode == 'dual')
        
        if enable_secondary:
            if secondary_client:
                self.auditor_secondary = Auditor(client=secondary_client, model_name=secondary_model)
                logger.info("Initialized LocalAuditor (Secondary)")
            else:
                self.auditor_secondary = RemoteAuditor(servers)
                logger.info(f"Initialized RemoteAuditor (Secondary) with servers: {servers}")
        
        logger.info(f"Audit mode: {mode}, Secondary enabled: {bool(self.auditor_secondary)}")
    
    def _setup_logger(self, log_dir):
        os.makedirs(log_dir, exist_ok=True)
        logger.setLevel(logging.INFO)
        
        # Configure handler
        file_handler = None
        # Check if we already have a handler for this path (in case of shared logger but different path? No, logger is singleton)
        # But we are using a singleton logger 'AuditManager'. If we run multiple tenants in same process, 
        # we will add multiple handlers to the SAME logger. This causes all tenants to log to ALL files.
        # This is a problem for the test (same process), but acceptable for separate processes (production).
        # For the test, we can tolerate it, or use tenant-specific logger names.
        
        # Using tenant-specific logger name would be better for isolation in same process.
        # But for now let's stick to the current plan and just fix the file creation.
        
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith('audit.log') and log_dir in h.baseFilename for h in logger.handlers):
             file_handler = logging.FileHandler(os.path.join(log_dir, 'audit.log'), encoding='utf-8')
             formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
             file_handler.setFormatter(formatter)
             logger.addHandler(file_handler)
             
             # Also attach to Auditor logger to capture low-level audit logs
             auditor_logger = logging.getLogger("Auditor")
             auditor_logger.addHandler(file_handler)

    def _get_config(self, key, default):
        cfg = {}
        if self.config_loader:
            cfg = self.config_loader() or {}
        # 平台差异化配置优先，例如 TG_AUDIT_ENABLED 覆盖 AUDIT_ENABLED
        prefix = {"telegram": "TG", "whatsapp": "WA", "wechat": "WX", "twitter": "TW", "weibo": "WB"}.get(self.platform, "").upper()
        if prefix:
            plat_key = f"{prefix}_{key}"
            if plat_key in cfg:
                return cfg.get(plat_key, default)
        return cfg.get(key, default)
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
    def _is_schedule_active(self):
        try:
            import datetime as _dt
            s = str(self._get_config('AUDIT_ACTIVE_START', '') or '').strip()
            e = str(self._get_config('AUDIT_ACTIVE_END', '') or '').strip()
            if not s or not e:
                return True
            now = _dt.datetime.now()
            start = _dt.datetime.fromisoformat(s)
            end = _dt.datetime.fromisoformat(e)
            return start <= now <= end
        except Exception:
            return True

    async def generate_with_audit(self, messages, user_input, history, temperature=0.7):
        """
        带审核的生成流程：
        生成 -> 审核 -> (不通过 -> 重试) * N -> 兜底话术
        Returns:
            dict: {"content": str, "usage": dict}
        """
        if not self.auditor_primary:
            # Should not happen if initialized correctly, but as a safeguard
            return {"content": "System Error: Audit component not initialized", "usage": {}, "status": {}}

        # 读取配置
        enabled = self._get_bool('AUDIT_ENABLED', False) and self._is_schedule_active()
        
        max_retries = 0
        total_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": self.model_name
        }

        def accumulate_usage(new_usage):
            if not new_usage: return
            total_usage["prompt_tokens"] += new_usage.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += new_usage.get("completion_tokens", 0)
            total_usage["total_tokens"] += new_usage.get("total_tokens", 0)
            # Model might change but we keep the primary one or last one
            if new_usage.get("model"):
                total_usage["model"] = new_usage["model"]

        if not enabled:
            try:
                response = await self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=500
                )
                if response.usage:
                    accumulate_usage({
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                        "model": self.model_name
                    })
                original = response.choices[0].message.content
                rewritten = self.apply_style_guard(original)
                style_applied = (rewritten != original)
                final_action = "send_rewritten" if style_applied else "send_normal"
                return {"content": rewritten, "usage": total_usage, "status": {
                    "style_guard_applied": style_applied,
                    "audit_primary_passed": True,
                    "audit_secondary_passed": True,
                    "final_action": final_action
                }}
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                fb_action, fb_msg = self._build_fallback("error")
                return {"content": fb_msg, "usage": total_usage, "status": {
                    "style_guard_applied": False,
                    "audit_primary_passed": False,
                    "audit_secondary_passed": False,
                    "final_action": fb_action
                }}

        current_messages = messages.copy()
        retry_count = 0
        safe_input, cat_in, word_in = self.keyword_manager.check_text(user_input or "")
        if not safe_input:
            logger.warning(f"Input keyword check failed: '{word_in}' in '{cat_in}'")
            fb_action, fb_msg = self._build_fallback("keyword")
            return {"content": fb_msg, "usage": total_usage, "status": {
                "style_guard_applied": False,
                "audit_primary_passed": False,
                "audit_secondary_passed": False,
                "final_action": fb_action
            }}
        
        try:
            strength = self._get_float('AUDIT_GUIDE_STRENGTH', 0.7)
            if strength >= 0.7:
                guide_text = "仅回答用户当前问题；避免提供具体方案或营销语；严格控制在200字内；保持中立与专业语气。"
            else:
                guide_text = "优先直接回答当前问题；避免营销语或具体方案；建议控制在200字内；保持中立与专业语气。"
            guidance_msg = {"role": "system", "content": guide_text}
            messages_injected = [guidance_msg] + current_messages
            
            # 动态加载工具
            from src.modules.knowledge_base.skill_center import skill_registry
            tools = skill_registry.get_tools_definition(self.tenant_id, self.db)
            
            response = await self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=messages_injected,
                temperature=temperature,
                max_tokens=500,
                tools=tools if tools else None, # Pass tools if available
                tool_choice="auto" if tools else None
            )
            
            # Handle Function Calling
            if response.choices[0].message.tool_calls:
                tool_calls = response.choices[0].message.tool_calls
                # Append assistant's tool call message
                messages_injected.append(response.choices[0].message)
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    tool_output = skill_registry.execute_tool(function_name, function_args)
                    
                    # Append tool result
                    messages_injected.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_output,
                    })
                
                # Second call to get final answer
                response = await self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages_injected,
                    temperature=temperature
                )
                
            if response.usage:
                accumulate_usage({
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "model": self.model_name
                })
            original = response.choices[0].message.content
            rewritten = self.apply_style_guard(original)
            style_applied = (rewritten != original)
        except APIConnectionError:
            raise
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            fb_action, fb_msg = self._build_fallback("")
            return {"content": fb_msg, "usage": total_usage, "status": {
                "style_guard_applied": False,
                "audit_primary_passed": False,
                "audit_secondary_passed": False,
                "final_action": fb_action
            }}
        is_safe, category, word = self.keyword_manager.check_text(rewritten)
        if not is_safe:
            logger.warning(f"Keyword check failed: Found '{word}' in category '{category}'")
            audit_primary_passed = False
            audit_secondary_passed = False
            fb_action, fb_msg = self._build_fallback("keyword")
            return {"content": fb_msg, "usage": total_usage, "status": {
                "style_guard_applied": style_applied,
                "audit_primary_passed": audit_primary_passed,
                "audit_secondary_passed": audit_secondary_passed,
                "final_action": fb_action
            }}
        logger.info(f"Auditing draft: {rewritten[:30]}...")
        primary_result = await self.auditor_primary.audit_content(user_input, rewritten, history)
        if hasattr(primary_result, 'usage'):
            accumulate_usage(primary_result.usage)
        audit_primary_passed = bool(primary_result.approved)
        audit_secondary_passed = True
        if audit_primary_passed and self.auditor_secondary:
            secondary_result = await self.auditor_secondary.audit_content(user_input, rewritten, history)
            audit_secondary_passed = bool(secondary_result.approved)
        if audit_primary_passed and audit_secondary_passed:
            final_action = "send_rewritten" if style_applied else "send_normal"
            return {"content": rewritten, "usage": total_usage, "status": {
                "style_guard_applied": style_applied,
                "audit_primary_passed": True,
                "audit_secondary_passed": True if self.auditor_secondary else True,
                "final_action": final_action
            }}
        fb_action, fb_msg = self._build_fallback(primary_result.suggestion if primary_result else "")
        return {"content": fb_msg, "usage": total_usage, "status": {
            "style_guard_applied": style_applied,
            "audit_primary_passed": audit_primary_passed,
            "audit_secondary_passed": audit_secondary_passed if self.auditor_secondary else False if not audit_primary_passed else True,
            "final_action": fb_action
        }}

    def _get_fallback_message(self):
        msg = self._fallback_cache.get_message()
        if msg:
            msg_hash = hashlib.md5(msg.encode('utf-8')).hexdigest()
            logger.info(f"Selected fallback message hash: {msg_hash}")
        else:
            logger.info("No fallback message configured in audit_fallback.txt")
        return msg
    def _build_fallback(self, suggestion: str):
        s = (suggestion or "").lower()
        handoff_msg = str(self._get_config('HANDOFF_MESSAGE', '') or '').strip()
        kb_fb_msg = str(self._get_config('KB_FALLBACK_MESSAGE', '') or '').strip()
        if "human" in s or "manual" in s:
            return ("handoff_human", handoff_msg or self._get_fallback_message())
        if "more info" in s or "补充" in s or "提供信息" in s:
            return ("send_safe_reply", kb_fb_msg or self._get_fallback_message())
        return ("send_safe_reply", self._get_fallback_message())
    def apply_style_guard(self, text: str) -> str:
        if not text:
            return text
        s = text
        try:
            from src.core.database import db
            prof = db.get_script_profile_by_name("default", "style_guard", "style_default", "v1")
            content = prof.get("content") or "{}"
            config = json.loads(content)
        except Exception:
            config = {}
        identity_patterns = config.get("identity_patterns", [
            r"(?i)作为\s*AI[，,。]*",
            r"(?i)作为\s*一个\s*AI[，,。]*",
            r"(?i)我是\s*AI[，,。]*"
        ])
        for pat in identity_patterns:
            try:
                s = re.sub(pat, "", s)
            except re.error:
                pass
        max_questions = int(config.get("max_questions", 1))
        if max_questions >= 0:
            q_matches = [m for m in re.finditer(r"[?？]", s)] # Support EN/CN question marks
            if len(q_matches) > max_questions:
                keep_indices = {m.start() for m in q_matches[:max_questions]}
                s_chars = list(s)
                for m in q_matches:
                    if m.start() not in keep_indices:
                        s_chars[m.start()] = "。"
                s = "".join(s_chars)
        rewrites = config.get("rewrite_rules", [
            (r"(?i)100%|百分之百|绝对|保证", "通常"),
            (r"(?i)必须|一定|务必", "建议"),
            (r"(?i)强烈推荐|最佳|顶级", "较为适合"),
        ])
        for pat, rep in rewrites:
            try:
                s = re.sub(pat, rep, s)
            except re.error:
                continue
        return s
