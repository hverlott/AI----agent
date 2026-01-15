import time
import unittest
import os
import json
from datetime import datetime
import sys
sys.path.append(os.path.dirname(__file__) + "/..")
from src.modules.knowledge_base.engine import KBEngine


class KnowledgeBasePerfTests(unittest.TestCase):
    def setUp(self):
        # Create synthetic large KB items in-memory
        self.items = []
        for i in range(2000):
            self.items.append({
                "id": f"synthetic_{i}",
                "title": f"条目 {i}",
                "category": "synthetic",
                "tags": ["perf"],
                "content": f"这是性能测试的合成内容段落，编号 {i}，包含关键词 审计 与 豁免。",
                "source_file": "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })

    def test_retrieval_latency(self):
        query = "资金审计与行政豁免"
        start = time.time()
        engine = KBEngine()
        hits = engine.retrieve_kb_context(query, self.items, topn=3)
        elapsed = (time.time() - start) * 1000
        # Ensure reasonable latency under 500ms on typical environment
        self.assertLess(elapsed, 500, f"检索耗时过长: {elapsed:.2f}ms")
        self.assertEqual(len(hits), 3)


if __name__ == "__main__":
    unittest.main()
