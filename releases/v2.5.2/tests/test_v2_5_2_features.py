import unittest
import json
from unittest.mock import MagicMock, patch
from src.modules.knowledge_base.skill_center import SkillRegistry, skill_registry
from src.modules.knowledge_base.engine import KBEngine

class TestV252Features(unittest.TestCase):
    
    def test_skill_registry_basic(self):
        """测试技能注册与执行"""
        registry = SkillRegistry()
        
        @registry.register_tool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {"arg": {"type": "string"}}}
        )
        def test_tool(arg):
            return f"Hello {arg}"
            
        # 1. 验证定义导出
        defs = registry.get_tools_definition()
        self.assertEqual(len(defs), 1)
        self.assertEqual(defs[0]["function"]["name"], "test_tool")
        
        # 2. 验证执行
        result = registry.execute_tool("test_tool", {"arg": "World"})
        self.assertEqual(result, "Hello World")
        
        # 3. 验证错误处理
        result_err = registry.execute_tool("non_existent", {})
        self.assertTrue("not found" in result_err)

    def test_calculator_skill(self):
        """测试内置计算器技能"""
        # 使用全局实例
        res = skill_registry.execute_tool("calculator", {"expression": "10 + 5 * 2"})
        self.assertEqual(res, "20")
        
        res_err = skill_registry.execute_tool("calculator", {"expression": "10 + abc"})
        self.assertTrue("Error" in res_err)

    def test_kb_hybrid_search_qa_match(self):
        """测试知识库 QA 精确匹配优先策略"""
        engine = KBEngine()
        
        # 构造模拟 KB Items
        items = [
            {
                "id": "1",
                "title": "Refund Policy", 
                "content": "Question: How to refund?\nAnswer: Go to settings page.",
                "category": "qa"
            },
            {
                "id": "2", 
                "title": "General Info", 
                "content": "Refunds are processed in 3 days.",
                "category": "text"
            }
        ]
        
        # 模拟 QA 匹配命中
        # match_qa_reply 依赖 normalize_text 等，这里直接测试逻辑流
        # 为了避免依赖 src.utils.text 的具体实现，我们 mock match_qa_reply
        engine.match_qa_reply = MagicMock(return_value="Go to settings page.")
        
        results = engine.retrieve_kb_context("How to refund?", items)
        
        # 预期：只返回 QA 匹配结果，且 score=1.0
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "QA Match")
        self.assertEqual(results[0]["content"], "Go to settings page.")
        self.assertEqual(results[0]["score"], 1.0)

    @patch('src.modules.knowledge_base.engine.KBEngine.load_vectors')
    @patch('src.modules.knowledge_base.engine.KBEngine._get_embedding')
    def test_kb_hybrid_search_fallback(self, mock_embed, mock_load_vectors):
        """测试混合检索降级逻辑"""
        engine = KBEngine()
        engine.client = MagicMock() # Mock OpenAI client existence
        
        # 模拟无 QA 匹配
        engine.match_qa_reply = MagicMock(return_value=None)
        
        # 模拟向量
        mock_load_vectors.return_value = {"1": [0.1, 0.2], "2": [0.9, 0.9]}
        mock_embed.return_value = [0.1, 0.2] # Query vector close to item 1
        
        # Mock _cosine_similarity to return high score for item 1
        # 简单起见，我们覆盖 _cosine_similarity
        engine._cosine_similarity = MagicMock(side_effect=lambda v1, v2: 0.9 if v1 == [0.1, 0.2] and v2 == [0.1, 0.2] else 0.1)
        
        items = [
            {"id": "1", "title": "Vector Match", "content": "This is vector match", "category": "text"},
            {"id": "2", "title": "Keyword Match", "content": "This is keyword match", "category": "text"}
        ]
        
        # 执行检索 (模拟 tenant_id='test')
        results = engine.retrieve_kb_context("keyword", items, tenant_id="test")
        
        # 验证结果：
        # 向量匹配应该命中 item 1 (mock score 0.9)
        # 关键词匹配 (keyword match) 应该命中 item 2
        # 混合结果应该包含两者
        
        ids = [it['id'] for it in results]
        # item 1 (Vector) and item 2 (Keyword) should both be present if topn allows
        # 注意: 我们的混合逻辑是先 Vector 后 Keyword，去重
        self.assertIn("1", ids) 
        # item 2 包含 "keyword" 单词，difflib 应该能匹配到
        # 如果 topn=3，两者都应该在
        
if __name__ == '__main__':
    unittest.main()
