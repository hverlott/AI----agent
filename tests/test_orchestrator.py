import unittest
import sys
import os

# Fix path to find modules in root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage_agent_runtime import StageAgentRuntime

class OrchestratorProviderTests(unittest.TestCase):
    def test_resolve_ai_provider_default(self):
        stager = StageAgentRuntime("default")
        p = stager.resolve_ai_provider({})
        self.assertTrue(p.get("base_url"))
        self.assertTrue(p.get("model"))
        self.assertGreaterEqual(int(p.get("timeout", 0)), 1)

if __name__ == "__main__":
    unittest.main()
