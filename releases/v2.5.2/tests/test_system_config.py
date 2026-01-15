
import sys
import os
import unittest
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.database import db

class TestSystemConfig(unittest.TestCase):
    def test_system_config(self):
        print("Testing System Config...")
        
        # Test default value
        val = db.get_system_config("non_existent_key", "default_val")
        self.assertEqual(val, "default_val")
        
        # Test set value
        db.set_system_config("test_key", "test_value")
        
        # Test get value
        val = db.get_system_config("test_key", "default_val")
        self.assertEqual(val, "test_value")
        
        # Test update value
        db.set_system_config("test_key", "new_value")
        val = db.get_system_config("test_key", "default_val")
        self.assertEqual(val, "new_value")
        
        print("System Config Test Passed!")

if __name__ == '__main__':
    unittest.main()
