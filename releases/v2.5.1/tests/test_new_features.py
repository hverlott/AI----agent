import unittest
import os
import shutil
import time
import re
from src.modules.telegram.whitelist_manager import WhitelistManager

class TestTelegramFeatures(unittest.TestCase):
    def setUp(self):
        self.test_tenant = "test_features_tenant"
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.wm = WhitelistManager(self.test_tenant, self.project_root)
        
        # Cleanup
        if os.path.exists(self.wm.cache_dir):
            shutil.rmtree(self.wm.cache_dir)
            
        self.wm._ensure_cache_dir()

    def tearDown(self):
        if os.path.exists(self.wm.cache_dir):
            shutil.rmtree(self.wm.cache_dir)

    def test_whitelist_management(self):
        # Test adding groups
        ids = ["1001", "1002"]
        self.wm.update_whitelist(ids)
        
        saved = self.wm.get_whitelist_ids()
        self.assertEqual(len(saved), 2)
        self.assertIn("1001", saved)
        
        # Test independent config
        config = {"auto_reply": True, "model": "gpt-4"}
        self.wm.update_group_config("1001", config)
        
        loaded_conf = self.wm.get_group_config("1001")
        self.assertEqual(loaded_conf["model"], "gpt-4")
        
        # Ensure update_whitelist doesn't wipe config
        self.wm.update_whitelist(["1001", "1003"])
        loaded_conf_after = self.wm.get_group_config("1001")
        self.assertEqual(loaded_conf_after["model"], "gpt-4")
        self.assertIn("1003", self.wm.get_whitelist_ids())

    def test_sender_name_filter_via_config(self):
        display = "User_推广_Agent"
        keys = [k.strip() for k in "推广,bot".split(",") if k.strip()]
        self.assertTrue(any(k.lower() in display.lower() for k in keys))
        display2 = "NormalUser"
        self.assertFalse(any(k.lower() in display2.lower() for k in keys))
        
    def test_whitelist_ids_persist(self):
        ids = ["1001", "1002"]
        self.wm.update_whitelist(ids)
        saved = self.wm.get_whitelist_ids()
        self.assertEqual(set(saved), set(ids))

if __name__ == '__main__':
    unittest.main()
