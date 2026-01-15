import json
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from datetime import datetime
from database import db

REPORT_FILE = os.path.join(BASE_DIR, "data", "logs", "save_logging_report.txt")
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

def _count_logs(tenant):
    return len(db.get_audit_logs(tenant, limit=10000))

def _last_log(tenant):
    rows = db.get_audit_logs(tenant, limit=1)
    return rows[0] if rows else {}

def _recent_actions(tenant, n=20):
    rows = db.get_audit_logs(tenant, limit=n)
    return [r.get("action") for r in rows]

def test_persona_save_audit():
    tenant = "test"
    before = _count_logs(tenant)
    db.upsert_script_profile(tenant, "persona", "calm_professional", "v1", json.dumps({"tone":"calm"}), True)
    db.log_audit(tenant, "Operator", "orch_persona_save", {"name": "calm_professional", "version": "v1"})
    after = _count_logs(tenant)
    assert after == before + 1
    last = _last_log(tenant)
    assert last.get("action") == "orch_persona_save"
    assert "details" in last
    with open(REPORT_FILE, "a", encoding="utf-8") as rf:
        rf.write("OK persona_save_audit\n")

def test_kb_add_update_delete_audit():
    tenant = "test"
    new_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    item = {
        "id": new_id,
        "tenant_id": tenant,
        "title": "测试条目",
        "category": "测试",
        "tags": json.dumps(["a","b"], ensure_ascii=False),
        "content": "正文",
        "source_file": "",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    db.add_kb_item(item)
    db.log_audit(tenant, "Operator", "kb_add", {"id": new_id, "title": "测试条目"})
    db.update_kb_item(new_id, {"title": "更新后", "updated_at": datetime.now().isoformat()})
    db.log_audit(tenant, "Operator", "kb_update", {"id": new_id, "title": "更新后"})
    db.delete_kb_item(new_id)
    db.log_audit(tenant, "Operator", "kb_delete", {"id": new_id})
    acts = _recent_actions(tenant, 10)
    assert "kb_delete" in acts
    with open(REPORT_FILE, "a", encoding="utf-8") as rf:
        rf.write("OK kb_add_update_delete_audit\n")

def test_platform_and_channel_config_audit():
    tenant = "test"
    db.log_audit(tenant, "Admin", "platform_config_save", {"platform": "telegram"})
    db.log_audit(tenant, "Admin", "tg_config_save", {"PRIVATE_REPLY": True, "GROUP_REPLY": True})
    db.log_audit(tenant, "Admin", "wa_config_save", {"private_reply": True, "group_reply": False})
    acts = _recent_actions(tenant, 10)
    assert any(a in ["platform_config_save", "tg_config_save", "wa_config_save"] for a in acts)
    with open(REPORT_FILE, "a", encoding="utf-8") as rf:
        rf.write("OK platform_and_channel_config_audit\n")

def test_system_env_session_audit():
    tenant = "test"
    db.log_audit(tenant, "Admin", "env_generate", {"tenant": tenant})
    db.log_audit(tenant, "Admin", "session_init", {"tenant": tenant})
    acts = _recent_actions(tenant, 10)
    assert any(a in ["env_generate", "session_init"] for a in acts)
    with open(REPORT_FILE, "a", encoding="utf-8") as rf:
        rf.write("OK system_env_session_audit\n")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    test_persona_save_audit()
    test_kb_add_update_delete_audit()
    test_platform_and_channel_config_audit()
    test_system_env_session_audit()
    print("All save logging tests passed. Report written to", REPORT_FILE)
