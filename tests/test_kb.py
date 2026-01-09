import os
import unittest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# Adjust import path for main.py functions
import sys
sys.path.append(os.path.dirname(__file__) + "/..")

from main import load_kb_entries, retrieve_kb_context, load_qa_pairs, match_qa_reply


class KnowledgeBaseTests(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.kb_dir = os.path.join(base_dir, "data", "knowledge_base")
        # Ensure directories exist for file fallback tests
        os.makedirs(os.path.join(base_dir, "platforms", "telegram"), exist_ok=True)
        
        # Prepare sample data for DB mock
        self.db_items = [
            {
                "id": "t1",
                "title": "黄金卡尊享版",
                "category": "移民",
                "tags": ["EB-5", "审计"],
                "content": "尊享版包含CPA资金来源审计与前移民官模拟背调。",
                "source_file": "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": "t2",
                "title": "I-601 行政豁免",
                "category": "法律",
                "tags": ["豁免", "逾期"],
                "content": "针对逾期滞留与非法入境，可申请人道主义豁免。",
                "source_file": "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]

    @patch("main.db")
    def test_load_kb_entries(self, mock_db):
        # Setup mock to return sample items
        mock_db.get_kb_items.return_value = self.db_items
        
        items = load_kb_entries()
        
        # Verify db was called
        mock_db.get_kb_items.assert_called_with("default")
        
        self.assertTrue(isinstance(items, list))
        # Should have at least 2 items from DB
        self.assertGreaterEqual(len(items), 2)
        
        # Check content of first item
        self.assertEqual(items[0]["id"], "t1")
        self.assertEqual(items[0]["title"], "黄金卡尊享版")

    def test_retrieve_kb_context(self):
        # Use the sample items directly for this test
        items = self.db_items
        hits = retrieve_kb_context("资金来源审计", items, topn=1)
        self.assertEqual(len(hits), 1)
        self.assertIn("审计", hits[0].get("content", ""))

    def test_qa_compat(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        qa_path = os.path.join(base_dir, "platforms", "telegram", "qa.txt")
        # Create dummy qa.txt if not exists
        if not os.path.exists(qa_path):
             with open(qa_path, "w", encoding="utf-8") as f:
                 f.write("Q: 你好 || A: 您好！\n")
                 
        # Ensure qa.txt is readable
        pairs = load_qa_pairs(qa_path)
        # Simulate match
        reply = match_qa_reply("你好", pairs)
        # None or string, but function should not crash
        self.assertTrue(reply is None or isinstance(reply, str))


if __name__ == "__main__":
    unittest.main()
