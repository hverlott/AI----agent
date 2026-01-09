import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Ensure project root is on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audit_manager import AuditManager

async def run_case(primary_pass: bool, secondary_pass: bool, style_change: bool):
    os.environ["OPENAI_API_KEY"] = "sk-test"
    os.environ["AI_BASE_URL"] = "http://dummy/v1"
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    # Mock generation reply
    gen_msg = "原始草稿？这是测试内容。"
    if style_change:
        gen_msg += " 我是AI。"
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=gen_msg))]
    mock_response.usage = MagicMock(prompt_tokens=50, completion_tokens=20, total_tokens=70)
    mock_client.chat.completions.create.return_value = mock_response

    am = AuditManager(mock_client, "test-model", config_loader=lambda: {
        "AUDIT_ENABLED": "True",
        "AUDIT_MODE": "dual",
        "AUDIT_SERVERS": "http://localhost:9000",
        "AUDIT_GUIDE_STRENGTH": "0.7"
    }, platform="telegram")

    # Patch auditors
    class _R:
        def __init__(self, ok):
            self.approved = ok
            self.suggestion = "" if ok else "more info needed"
            self.usage = {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
    async def _audit_ok(*args, **kwargs):
        return _R(True)
    async def _audit_fail(*args, **kwargs):
        return _R(False)

    am.auditor_primary.audit_content = _audit_ok if primary_pass else _audit_fail
    am.auditor_secondary = MagicMock()
    am.auditor_secondary.audit_content = _audit_ok if secondary_pass else _audit_fail

    result = await am.generate_with_audit(
        messages=[{"role":"system","content":"sys"}],
        user_input="测试用户输入",
        history=[]
    )
    return result

async def main():
    print("Case A: primary PASS, secondary PASS")
    resA = await run_case(True, True, True)
    print(resA["status"])
    assert resA["status"]["audit_primary_passed"] and resA["status"]["audit_secondary_passed"]
    assert resA["status"]["final_action"] in ("send_rewritten","send_normal")

    print("Case B: primary PASS, secondary FAIL")
    resB = await run_case(True, False, False)
    print(resB["status"])
    assert resB["status"]["final_action"] == "send_safe_reply"
    assert not resB["status"]["audit_secondary_passed"]

    print("Case C: primary FAIL")
    resC = await run_case(False, True, True)
    print(resC["status"])
    assert resC["status"]["final_action"] == "send_safe_reply"
    assert not resC["status"]["audit_primary_passed"]

    print("All dual-audit tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
