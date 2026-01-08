import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta

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
    now = datetime.now()
    # Window active
    cfg_active = {
        "AUDIT_ENABLED": "True",
        "AUDIT_MODE": "local",
        "AUDIT_ACTIVE_START": (now - timedelta(minutes=1)).isoformat(),
        "AUDIT_ACTIVE_END": (now + timedelta(minutes=1)).isoformat(),
    }
    am_active = AuditManager(mock_client, "test-model", config_loader=lambda: cfg_active, platform="telegram")
    # Patch auditor to PASS
    class _R: 
        def __init__(self): 
            self.approved = True; self.suggestion=""; self.usage={"total_tokens":1}
    async def _audit_ok(*args, **kwargs): return _R()
    am_active.auditor_primary.audit_content = _audit_ok
    res1 = await am_active.generate_with_audit([{"role":"system","content":"sys"}], "msg", [])
    assert res1["status"]["final_action"] in ("send_normal","send_rewritten")
    # Window inactive -> audit disabled path
    cfg_inactive = {
        "AUDIT_ENABLED": "True",
        "AUDIT_MODE": "local",
        "AUDIT_ACTIVE_START": (now - timedelta(hours=2)).isoformat(),
        "AUDIT_ACTIVE_END": (now - timedelta(hours=1)).isoformat(),
    }
    am_inactive = AuditManager(mock_client, "test-model", config_loader=lambda: cfg_inactive, platform="telegram")
    res2 = await am_inactive.generate_with_audit([{"role":"system","content":"sys"}], "msg", [])
    # When disabled, we still send after style guard, with "audit primary/secondary passed"=True to indicate bypass
    assert res2["status"]["final_action"] in ("send_normal","send_rewritten")
    print("Schedule audit tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
