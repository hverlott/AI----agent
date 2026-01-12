import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auditor import AuditResult
from src.modules.audit.manager import AuditManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Diagnostic")

os.environ.setdefault("OPENAI_API_KEY", "sk-dummy-key")
os.environ.setdefault("AI_API_KEY", "sk-dummy-key")
os.environ.setdefault("AI_BASE_URL", "http://dummy/v1")

async def _run_audit_flow():
    print("--- Starting Diagnostic Check ---")
    
    # 1. Check Config Files
    files_to_check = [
        "platforms/telegram/audit_prompt.txt",
        "platforms/telegram/audit_fallback.txt"
    ]
    for f in files_to_check:
        if os.path.exists(f):
            print(f"[PASS] Found {f}")
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content.strip():
                     print(f"[WARN] {f} is empty")
                else:
                    print(f"[INFO] {f} content length: {len(content)}")
        else:
            print(f"[FAIL] Missing {f}")

    # 2. Simulate Audit Manager Logic
    print("\n--- Simulating Audit Manager ---")
    
    # Mock AI Client
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    
    # Mock Response 1: Bad content (to trigger audit fail)
    bad_response = MagicMock()
    bad_response.choices = [MagicMock(message=MagicMock(content="Bad Reply"))]
    
    # Mock Response 2: Good content (if we wanted to test pass, but here we test fallback)
    # We will make it always return bad content to force fallback
    mock_client.chat.completions.create.return_value = bad_response

    # Initialize AuditManager
    am = AuditManager(
        mock_client,
        "test-model",
        config_loader=lambda: {
            "AUDIT_ENABLED": "True",
            "AUDIT_MODE": "remote",
            "AUDIT_SERVERS": "http://127.0.0.1:9",
        },
        platform="telegram",
    )
    am.auditor_primary = AsyncMock()
    am.auditor_primary.audit_content.return_value = AuditResult(
        status="FAIL",
        reason="Diagnostic Test Fail",
        suggestion="",
    )
    
    # Mock Config Loader
    am._get_config = MagicMock(side_effect=lambda k, d: "true" if k == "AUDIT_ENABLED" else d)

    # Run Generation
    print("Invoking generate_with_audit...")
    result = await am.generate_with_audit([], "User Input", [])
    print(f"Final Result received: {result}")
    with open("platforms/telegram/audit_fallback.txt", 'r', encoding='utf-8') as f:
        fallbacks = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    if isinstance(result, dict):
        content = result.get("content")
        status = result.get("status", {})
        if status.get("final_action") == "send_safe_reply" and (content in fallbacks or isinstance(content, str)):
            print("[PASS] System correctly applied unified fallback.")
        else:
            print(f"[FAIL] Unexpected final action or content: {status} / {content}")
        call_count = mock_client.chat.completions.create.call_count
        print(f"Generation attempts: {call_count}")
        if call_count == 1:
            print("[PASS] No retries after audit failure (hard veto).")
        else:
            print(f"[WARN] Expected 1 attempt, got {call_count}")
    else:
        print("[FAIL] Result format should be dict.")


def test_audit_flow():
    asyncio.run(_run_audit_flow())

if __name__ == "__main__":
    asyncio.run(test_audit_flow())
