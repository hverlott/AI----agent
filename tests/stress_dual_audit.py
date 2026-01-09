import asyncio
import os
import sys
import random
from unittest.mock import MagicMock, AsyncMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from audit_manager import AuditManager

async def run_once(seed):
    os.environ["OPENAI_API_KEY"] = "sk-test"
    os.environ["AI_BASE_URL"] = "http://dummy/v1"
    rnd = random.Random(seed)
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    gen_msg = "测试草稿？内容正常。"
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=gen_msg))]
    mock_response.usage = MagicMock(prompt_tokens=20, completion_tokens=10, total_tokens=30)
    mock_client.chat.completions.create.return_value = mock_response
    am = AuditManager(mock_client, "test-model", config_loader=lambda: {
        "AUDIT_ENABLED": "True",
        "AUDIT_MODE": "dual",
        "AUDIT_SERVERS": "http://localhost:9000",
        "AUDIT_GUIDE_STRENGTH": "0.7"
    }, platform="telegram")
    class _R:
        def __init__(self, ok):
            self.approved = ok
            self.suggestion = "" if ok else "more info needed"
            self.usage = {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3}
    async def _audit(*args, **kwargs):
        return _R(rnd.random() > 0.3)  # 70% 通过率
    am.auditor_primary.audit_content = _audit
    am.auditor_secondary = MagicMock()
    am.auditor_secondary.audit_content = _audit
    res = await am.generate_with_audit([{"role":"system","content":"sys"}], "消息", [])
    return res["status"]["final_action"]

async def main():
    N = 50
    final_actions = await asyncio.gather(*[run_once(i) for i in range(N)])
    safe = sum(1 for a in final_actions if a == "send_safe_reply")
    normal = sum(1 for a in final_actions if a in ("send_normal","send_rewritten"))
    print(f"Total: {N}, safe_fallback: {safe}, pass_send: {normal}")
    assert safe + normal == N
    print("Stress test passed.")

if __name__ == "__main__":
    asyncio.run(main())
