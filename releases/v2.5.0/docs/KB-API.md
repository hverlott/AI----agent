# 知识库 API 文档

## 概述
- 存储位置：data/knowledge_base/db.json 与 data/knowledge_base/files/
- 结构：db.json 采用 items 数组，每个元素为知识条目

## 数据结构
```json
{
  "items": [
    {
      "id": "20260105123000123456",
      "title": "示例标题",
      "category": "分类",
      "tags": ["标签A", "标签B"],
      "content": "纯文本内容",
      "source_file": "data/knowledge_base/files/example.pdf",
      "parse_note": "parsed:pdf",
      "created_at": "2026-01-05T12:30:00.123456",
      "updated_at": "2026-01-05T12:30:00.123456"
    }
  ]
}
```

## 管理后台接口（Streamlit 事件）
- 创建条目：在“管理”页填写标题/分类/标签/内容，点击保存
- 导入条目：在“导入”页上传文件，解析后保存为条目
- 编辑/删除：在“管理”页对列表条目执行编辑和删除

## 检索接口
- 函数：main.py 中 retrieve_kb_context(query_text, kb_items, topn=2)
- 输入：query_text 字符串；kb_items 为 load_kb_entries() 返回的条目列表
- 输出：按相似度排序的前 N 个条目，用于注入到 AI 会话的 system 上下文

## 集成点
- main.py handler 中在 QA 未命中时，自动注入知识库上下文至 system 提示词

