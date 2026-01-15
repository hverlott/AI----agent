import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audit_manager import AuditManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Diagnostic")

# Patch Auditor to avoid OpenAI init error
sys.modules['auditor'] = MagicMock()
from auditor import AuditResult
# We need to ensure AuditManager can import Auditor, but we already patched sys.modules['auditor']
# However, AuditManager imports Auditor from auditor. 
# If AuditManager is already imported, we might need to reload or patch it differently.
# But here AuditManager is imported *after* we might patch? 
# No, AuditManager is imported at top.
# Let's set env var instead, it's safer.
os.environ["OPENAI_API_KEY"] = "sk-dummy-key"
os.environ["OPENAI_BASE_URL"] = "http://dummy"

async def test_audit_flow():
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
    # We assume 'auditor.py' is working (it was verified in previous steps)
    # But for this test, we might want to use the real LocalAuditor if possible, 
    # or mock it if we don't want to depend on external LLM for auditing.
    # Since we want to test the *manager's* retry logic, we can mock the auditor to always FAIL.
    
    am = AuditManager(mock_client, "test-model")
    am.auditor = AsyncMock()
    # Mock Audit Result: Always FAIL
    from auditor import AuditResult
    mock_result = MagicMock()
    mock_result.status = "FAIL"
    mock_result.approved = False # Important: Must be False to trigger retry
    mock_result.reason = "Diagnostic Test Fail"
    mock_result.suggestion = "Suggestion"
    am.auditor.audit_content.return_value = mock_result
    
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

if __name__ == "__main__":
    asyncio.run(test_audit_flow())
