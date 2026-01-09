import unittest
from database import db
from conversation_state_manager import ConversationStateManager
import json

class TestConversationState(unittest.TestCase):
    def setUp(self):
        self.tenant = "default"
        self.platform = "tg"
        self.user = "u_123"
        try:
            db.execute_update("DELETE FROM conversation_states WHERE tenant_id = ? AND platform = ? AND user_id = ?", (self.tenant, self.platform, self.user))
        except:
            pass
    def test_upsert_and_get_state(self):
        m = ConversationStateManager(self.tenant)
        s0 = m.get_state(self.platform, self.user)
        self.assertEqual(s0["current_stage"], "S0")
        s0["current_stage"] = "S1"
        s0["intent_score"] = 0.65
        s0["slots"] = {"need": "demo"}
        m.update_state(self.platform, self.user, s0)
        s1 = m.get_state(self.platform, self.user)
        self.assertEqual(s1["current_stage"], "S1")
        self.assertAlmostEqual(s1["intent_score"], 0.65, places=2)
        self.assertEqual(s1["slots"]["need"], "demo")
    def test_script_profiles_crud(self):
        db.upsert_script_profile(self.tenant, "persona", "calm_professional", "v1", json.dumps({"tone":"calm"}), True)
        rows = db.get_script_profiles(self.tenant, "persona")
        self.assertTrue(len(rows) >= 1)
        prof = db.get_script_profile_by_name(self.tenant, "persona", "calm_professional", "v1")
        self.assertTrue(bool(prof))

if __name__ == "__main__":
    unittest.main()
