import os
import json
import httpx
from openai import AsyncOpenAI
import logging

# 统一审核日志编码与路径
_AUDIT_LOG_DIR = os.path.join("platforms", "telegram", "logs")
os.makedirs(_AUDIT_LOG_DIR, exist_ok=True)
_logger = logging.getLogger("Auditor")
_logger.setLevel(logging.INFO)
if _logger.hasHandlers():
    _logger.handlers.clear()
_fh = logging.FileHandler(os.path.join(_AUDIT_LOG_DIR, "audit.log"), encoding="utf-8")
_fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
_logger.addHandler(_fh)

class AuditResult:
    def __init__(self, status: str, reason: str, suggestion: str = "", usage: dict = None):
        self.status = status
        self.reason = reason
        self.suggestion = suggestion
        self.usage = usage or {}
        # 严格校验：只有全大写 PASS 才是通过
        self.approved = (status.strip() == "PASS")

    def __str__(self):
        return f"Status: {self.status} (Approved: {self.approved}), Reason: {self.reason}, Suggestion: {self.suggestion}, Usage: {self.usage}"

    def to_dict(self):
        return {
            "status": self.status,
            "approved": self.approved,
            "reason": self.reason,
            "suggestion": self.suggestion,
            "usage": self.usage
        }

class Auditor:
    def __init__(self, client=None, api_key=None, base_url=None, model_name=None):
        self.model_name = model_name or os.getenv('AI_MODEL_NAME')
        
        if client:
            self.client = client
        else:
            self.api_key = api_key or os.getenv('AI_API_KEY')
            self.base_url = base_url or os.getenv('AI_BASE_URL')
            
            # 自动修复 URL 逻辑（复用 main.py 的逻辑）
            if self.base_url:
                if not self.base_url.startswith("http"):
                    self.base_url = f"https://{self.base_url}"
                if "://55.ai" in self.base_url:
                    self.base_url = self.base_url.replace("://55.ai", "://api.55.ai")
                if "/chat/completions" in self.base_url:
                    self.base_url = self.base_url.replace("/chat/completions", "")
                if not self.base_url.endswith("/v1"):
                    self.base_url = self.base_url.rstrip("/") + "/v1"

            # 初始化客户端
            _v = (os.getenv("HTTPX_VERIFY_SSL") or "").strip().lower()
            _verify = False if _v in ("0","false","no") else True
            http_client = httpx.AsyncClient(verify=_verify)
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client
            )
        
        # 加载 Prompt
        self.prompt_path = os.path.join(os.path.dirname(__file__), 'platforms', 'telegram', 'audit_prompt.txt')
        self.system_prompt = self._load_prompt()

    def _load_prompt(self):
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            _logger.error(f"Failed to load audit prompt: {e}")
            return "You are an AI content auditor. Respond in JSON with status('PASS'/'FAIL'), reason(str), suggestion(str)."

    async def audit_content(self, user_input, draft_reply, history) -> AuditResult:
        """
        审核内容
        """
        audit_payload = {
            "user_input": user_input,
            "draft_reply": draft_reply,
            "history": str(history[-5:]) # 只取最近 5 条历史以节省 token
        }
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(audit_payload, ensure_ascii=False)}
        ]

        try:
            _logger.info(f"Auditing content for user input: {user_input[:20]}...")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0, # 审核需要精确
                response_format={"type": "json_object"} # 强制 JSON 模式（如果模型支持）
            )
            
            content = response.choices[0].message.content
            _logger.info(f"Audit response: {content}")
            
            # Capture usage
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "model": self.model_name
                }

            try:
                result_json = json.loads(content)
                # 兼容旧格式 approved 字段，如果 status 不存在
                status = result_json.get('status', '')
                if not status and 'approved' in result_json:
                     status = "PASS" if result_json['approved'] else "FAIL"
                
                return AuditResult(
                    status=status,
                    reason=result_json.get('reason', 'No reason provided'),
                    suggestion=result_json.get('suggestion', ''),
                    usage=usage
                )
            except json.JSONDecodeError:
                _logger.error(f"Failed to parse audit response JSON: {content}")
                return AuditResult("FAIL", "JSON Parse Error", "System Error")
                
        except Exception as e:
            _logger.error(f"Audit API call failed: {e}")
            # Fail-Open or Fail-Closed? Previous code was Fail-Open.
            # User wants strict verification. If system fails, maybe it should be FAIL?
            # But usually Fail-Open is better for availability.
            # However, user emphasized "Only execute send when regulatory system returns PASS".
            # This implies Fail-Closed on system error?
            # But the previous requirement was Fail-Open.
            # Let's stick to returning an error status but maybe "FAIL" to be safe if strict.
            # Or "PASS" if we want to prioritize availability.
            # Let's return FAIL with System Error.
            return AuditResult("FAIL", f"Audit System Error: {str(e)}", "System Error")


# 模拟双机热备的健康检查接口
async def health_check():
    return {"status": "healthy", "service": "auditor-primary"}
