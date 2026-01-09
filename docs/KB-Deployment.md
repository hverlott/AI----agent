# 知识库部署与回滚方案

## 部署步骤
- 确认 Python 依赖满足 requirements.txt
- 可选安装解析依赖：PyPDF2、python-docx、openpyxl
- 启动管理后台：start_multi_admin.bat 或 `python -m streamlit run admin_multi.py`
- 在“📚 数据管理 > 知识库”面板创建/导入条目

## 数据存储
- 路径：data/knowledge_base/db.json 与 data/knowledge_base/files/
- 备份：定期复制 db.json 与 files/ 至安全位置

## 回滚方案
- 当出现异常时，可将 db.json 与 files/ 目录替换为上一次备份版本
- 管理后台不需要重启即可生效（文件保存后即读取）

## 影响分析
- 新增模块为独立面板，不影响 Telegram/WhatsApp 现有功能
- main.py 仅在 QA 未命中时读取知识库上下文，兼容性良好
