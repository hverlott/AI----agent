import unittest
import os
import sys
import sqlite3
import json
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.modules.telegram.filter_manager import check_content_filter
from src.modules.knowledge_base.skill_center import SkillRegistry
from src.core.database import DatabaseManager

class TestRegressionV252(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Setup temporary DB
        cls.db_path = "tests/test_regression.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db = DatabaseManager(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    # --- 1. Content Filter Tests ---
    def test_content_filter_logic(self):
        """Verify content filter keyword density logic"""
        config = {
            "CONTENT_FILTER": {
                "enabled": True,
                "rules": [
                    {"keyword": "加群", "threshold": 0.5}
                ]
            }
        }
        
        # Case 1: High density (Blocked)
        # "加群加群" -> 4 chars, 4 chars match -> 1.0 > 0.5
        is_filtered, kw = check_content_filter("加群加群", config)
        self.assertTrue(is_filtered)
        self.assertEqual(kw, "加群")
        
        # Case 2: Low density (Allowed)
        # "你好我想加群" -> 6 chars, 2 chars match -> 0.33 < 0.5
        is_filtered, kw = check_content_filter("你好我想加群", config)
        self.assertFalse(is_filtered)
        
        # Case 3: Disabled
        config["CONTENT_FILTER"]["enabled"] = False
        is_filtered, kw = check_content_filter("加群加群", config)
        self.assertFalse(is_filtered)

    # --- 2. Skill Center Tests ---
    def test_skill_db_crud(self):
        """Verify Skill Center Database Operations"""
        tenant_id = "test_tenant"
        skill_data = {
            "id": "skill_calc",
            "name": "Calculator",
            "description": "Simple Calc",
            "enabled": True,
            "bound_ai_id": "gpt-4",
            "config": {"type": "prompt", "content": "You are a calc"}
        }
        
        # Create/Upsert
        self.db.upsert_skill(tenant_id, skill_data)
        
        # Read
        skills = self.db.list_skills(tenant_id)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]["id"], "skill_calc")
        self.assertEqual(skills[0]["config"]["type"], "prompt")
        
        # Update
        skill_data["enabled"] = False
        self.db.upsert_skill(tenant_id, skill_data)
        skills_v2 = self.db.list_skills(tenant_id)
        self.assertEqual(skills_v2[0]["enabled"], 0)
        
        # Delete
        self.db.delete_skill(tenant_id, "skill_calc")
        skills_v3 = self.db.list_skills(tenant_id)
        self.assertEqual(len(skills_v3), 0)

    # --- 3. Database Index Tests ---
    def test_database_indexes(self):
        """Verify if new indexes exist in SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA index_list(message_events)")
        indexes = [row[1] for row in cursor.fetchall()]
        
        expected_indexes = [
            "idx_msg_tenant_time",
            "idx_msg_learning",
            "idx_msg_chat"
        ]
        
        for idx in expected_indexes:
            self.assertIn(idx, indexes, f"Index {idx} is missing")
            
        conn.close()

    # --- 4. Regression: Tenant Config Loading ---
    def test_tenant_config_loading_priority(self):
        """Verify DB config priority over file (mocked)"""
        # Inject config into DB
        tenant_id = "default"
        db_conf = {"PRIVATE_REPLY": "off", "AI_TEMPERATURE": 0.5}
        self.db.upsert_tenant_config(tenant_id, db_conf)
        
        # Mock loader
        from src.config.loader import ConfigManager
        
        # We need to patch DatabaseManager global instance or pass our db instance
        # ConfigManager uses `from src.core.database import db`
        
        with patch('src.core.database.db', self.db):
            loader = ConfigManager(tenant_id)
            # Mock file existence to avoid reading real file
            loader._get_readable_path = MagicMock(return_value="non_existent_file.txt")
            
            # The loader should pick up DB config
            config = loader.load_config()
            
            self.assertFalse(config['PRIVATE_REPLY']) # Should be False (off)
            self.assertEqual(config['AI_TEMPERATURE'], 0.5)

if __name__ == '__main__':
    unittest.main()
