import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from audit_manager import AuditManager

async def main():
    os.environ["OPENAI_API_KEY"] = "sk-test"
    os.environ["AI_BASE_URL"] = "http://dummy/v1"
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content="内容"))]
    resp.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    mock_client.chat.completions.create.return_value = resp
    cfg = {
        "AUDIT_ENABLED": "True",
        "TG_AUDIT_ENABLED": "False",  # disable for telegram
        "AUDIT_MODE": "dual",
        "AUDIT_SERVERS": "http://localhost:9000",
    }
    am = AuditManager(mock_client, "test-model", config_loader=lambda: cfg, platform="telegram")
    res = await am.generate_with_audit([{"role":"system","content":"sys"}], "msg", [])
    assert res["status"]["final_action"] in ("send_normal","send_rewritten")
    assert res["status"]["audit_primary_passed"] and res["status"]["audit_secondary_passed"]
    print("Platform toggle test passed.")

if __name__ == "__main__":
    asyncio.run(main())
