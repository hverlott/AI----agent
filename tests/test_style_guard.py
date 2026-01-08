import unittest
from audit_manager import AuditManager

class StyleGuardTests(unittest.TestCase):
    def test_remove_ai_identity_and_limit_questions(self):
        cfg = lambda: {"AUDIT_MODE": "remote"}
        mgr = AuditManager(ai_client=None, model_name="none", config_loader=cfg)
        text = "作为AI，我可以帮你吗?? 还有其他问题吗??"
        out = mgr.apply_style_guard(text)
        self.assertNotIn("作为AI", out)
        self.assertEqual(out.count("?"), 1)

if __name__ == "__main__":
    unittest.main()
