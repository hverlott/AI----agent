import unittest
import os
import sys

# Add parent dir to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from auth_core import AuthManager

class TestSaaSIsolation(unittest.TestCase):
    def setUp(self):
        # Use a temporary DB for testing
        self.test_db_path = "data/test_saas_isolation.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        self.db = DatabaseManager(self.test_db_path)
        self.auth = AuthManager(self.db)
        
        # Setup Tenants
        self.db.create_tenant("tenant_a", "standard")
        self.db.create_tenant("tenant_b", "standard")
        
        # Setup Users
        self.auth.create_user("admin_a", "pass", "business_admin", "tenant_a")
        self.auth.create_user("admin_b", "pass", "business_admin", "tenant_b")

    def tearDown(self):
        try:
            self.db._get_conn().close()
        except:
            pass
            
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except:
                pass

    def test_data_isolation(self):
        # 1. Insert data for Tenant A
        self.db.record_message_event(
            tenant_id="tenant_a", 
            platform="telegram", 
            chat_id="123", 
            direction="in", 
            status="success",
            tokens_used=100,
            cost=0.01
        )
        
        # 2. Check Metrics for Tenant A (Should have data)
        metrics_a = self.db.get_dashboard_metrics("tenant_a")
        self.assertEqual(metrics_a['total_tokens'], 100)
        self.assertEqual(metrics_a['total_cost'], 0.01)
        
        # 3. Check Metrics for Tenant B (Should be empty)
        metrics_b = self.db.get_dashboard_metrics("tenant_b")
        self.assertEqual(metrics_b['total_tokens'], 0)
        self.assertEqual(metrics_b['total_cost'], 0.0)
        
    def test_config_isolation(self):
        # 1. Set Config for Tenant A
        conf_a = {"bot_name": "Bot A", "welcome": "Hi from A"}
        self.db.upsert_tenant_config("tenant_a", conf_a)
        
        # 2. Set Config for Tenant B
        conf_b = {"bot_name": "Bot B", "welcome": "Hi from B"}
        self.db.upsert_tenant_config("tenant_b", conf_b)
        
        # 3. Verify Retrieval
        get_a = self.db.get_tenant_config("tenant_a")
        get_b = self.db.get_tenant_config("tenant_b")
        
        self.assertEqual(get_a['bot_name'], "Bot A")
        self.assertEqual(get_b['bot_name'], "Bot B")
        self.assertNotEqual(get_a['bot_name'], get_b['bot_name'])

    def test_user_binding(self):
        # Verify users are bound to correct tenants
        user_a = self.db.get_user_by_username("admin_a")
        user_b = self.db.get_user_by_username("admin_b")
        
        self.assertEqual(user_a['tenant_id'], "tenant_a")
        self.assertEqual(user_b['tenant_id'], "tenant_b")

if __name__ == '__main__':
    unittest.main()
