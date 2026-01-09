import unittest
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyword_manager import KeywordManager

class TestKeywordManager(unittest.TestCase):
    def setUp(self):
        self.test_file = "tests/test_keywords.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.km = KeywordManager(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_add_remove_keyword(self):
        # Test Add
        success, msg = self.km.add_keyword("block", "badword")
        self.assertTrue(success)
        self.assertIn("badword", self.km.get_keywords()["block"])

        # Test Duplicate
        success, msg = self.km.add_keyword("block", "badword")
        self.assertFalse(success)

        # Test Remove
        success, msg = self.km.remove_keyword("block", "badword")
        self.assertTrue(success)
        self.assertNotIn("badword", self.km.get_keywords()["block"])

    def test_check_text(self):
        self.km.add_keyword("block", "blockword")
        self.km.add_keyword("sensitive", "senseword")

        # Test Safe
        safe, cat, word = self.km.check_text("This is safe")
        self.assertTrue(safe)
        self.assertIsNone(cat)

        # Test Block
        safe, cat, word = self.km.check_text("This contains blockword")
        self.assertFalse(safe)
        self.assertEqual(cat, "block")
        self.assertEqual(word, "blockword")

        # Test Sensitive
        safe, cat, word = self.km.check_text("This contains senseword")
        self.assertFalse(safe)
        self.assertEqual(cat, "sensitive")
        self.assertEqual(word, "senseword")

    def test_performance(self):
        import time
        # Add 100 keywords
        for i in range(100):
            self.km.add_keyword("block", f"badword{i}")
        
        start = time.time()
        # Check 10000 times
        for _ in range(10000):
            self.km.check_text("This is a safe text without any bad words hopefully.")
        elapsed = time.time() - start
        
        # Should be very fast (e.g. < 1 second for 10k checks)
        print(f"10k checks took {elapsed:.4f}s")
        self.assertLess(elapsed, 1.0)

    def test_rename_keyword(self):
        self.km.add_keyword("block", "oldword")
        ok, msg = self.km.rename_keyword("block", "oldword", "newword")
        self.assertTrue(ok)
        self.assertIn("newword", self.km.get_keywords()["block"])
        self.assertNotIn("oldword", self.km.get_keywords()["block"])

    def test_allowlist_precedence(self):
        self.km.add_keyword("block", "ZHU PENG")
        self.km.add_keyword("allow", "ZHU PENG")
        safe, cat, word = self.km.check_text("我是 ZHU PENG 首席顾问")
        self.assertTrue(safe)
        self.assertEqual(cat, "allow")
        self.assertEqual(word, "ZHU PENG")

if __name__ == '__main__':
    unittest.main()
