import unittest
import os
import json
import shutil
from datetime import datetime
from src.modules.telegram.whitelist_manager import WhitelistManager

class TestWhitelistManager(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "test_tenant"
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.cache_dir = os.path.join(self.root_dir, "cache", "group_whitelist")
        self.cache_file = os.path.join(self.cache_dir, f"whitelist_{self.tenant_id}.json")
        
        # Clean up before test
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            
        self.wm = WhitelistManager(self.tenant_id, self.root_dir)

    def tearDown(self):
        # Clean up after test
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def test_init_creates_directory_and_empty_file(self):
        """Test that initialization creates the directory."""
        # Initializing WhitelistManager in setUp should trigger ensure_cache_dir
        self.assertTrue(os.path.exists(self.cache_dir))
        
        # Load should return empty dict and create file
        data = self.wm.load_whitelist()
        self.assertEqual(data, {})
        self.assertTrue(os.path.exists(self.cache_file))

    def test_update_whitelist(self):
        """Test adding and updating whitelist items."""
        group_ids = ["123", "456"]
        self.wm.update_whitelist(group_ids)
        
        data = self.wm.load_whitelist()
        self.assertIn("123", data)
        self.assertIn("456", data)
        self.assertTrue(data["123"]["status"])
        self.assertTrue(data["456"]["status"])
        self.assertIn("updated_at", data["123"])

        # Update: Remove 456, Add 789
        new_ids = ["123", "789"]
        self.wm.update_whitelist(new_ids)
        
        data = self.wm.load_whitelist()
        self.assertTrue(data["123"]["status"])
        self.assertTrue(data["789"]["status"])
        # 456 should be present but status False
        self.assertIn("456", data)
        self.assertFalse(data["456"]["status"])

    def test_get_whitelist_ids(self):
        """Test retrieving only active IDs."""
        self.wm.update_whitelist(["123", "456"])
        self.wm.update_whitelist(["123"]) # 456 becomes False
        
        ids = self.wm.get_whitelist_ids()
        self.assertIn("123", ids)
        self.assertNotIn("456", ids)
        self.assertEqual(len(ids), 1)

    def test_corrupt_cache_recovery(self):
        """Test recovery from corrupted JSON file."""
        # Create a valid cache first
        self.wm.update_whitelist(["123"])
        
        # Corrupt the file
        with open(self.cache_file, "w") as f:
            f.write("{invalid_json")
            
        # Load should return empty dict (re-init)
        data = self.wm.load_whitelist()
        self.assertEqual(data, {})
        
        # File should be overwritten with valid empty JSON
        with open(self.cache_file, "r") as f:
            content = json.load(f)
        self.assertEqual(content, {})

    def test_add_remove_single(self):
        """Test single add/remove operations."""
        self.wm.add_group("999")
        ids = self.wm.get_whitelist_ids()
        self.assertIn("999", ids)
        
        self.wm.remove_group("999")
        ids = self.wm.get_whitelist_ids()
        self.assertNotIn("999", ids)
        
        data = self.wm.load_whitelist()
        self.assertFalse(data["999"]["status"])

if __name__ == '__main__':
    unittest.main()
