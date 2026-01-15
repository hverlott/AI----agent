import os
import json
import uuid
import re
from datetime import datetime
from src.utils.text import normalize_text

class KBLoader:
    def __init__(self, config_manager, logger, db):
        self.cfg = config_manager
        self.logger = logger
        self.db = db
        self.tenant_id = config_manager.tenant_id

    def load_kb_entries(self):
        """
        加载知识库条目：优先从 SQLite 数据库加载
        支持 KB_REFRESH=on 强制刷新
        如果数据库为空，则尝试从本地 Knowledge Base.txt 自动解析并导入
        """
        items = []
        
        try:
            # 0. 检查刷新指令或异常状态
            config = self.cfg.load_config()
            kb_refresh = str(config.get("KB_REFRESH", "off")).lower() == "on"
            need_reload = kb_refresh

            if not need_reload:
                db_items = self.db.get_kb_items(self.tenant_id)
                if db_items and len(db_items) == 1:
                    row = db_items[0]
                    content_len = len(row.get("content", "") or "")
                    tags_raw = row.get("tags") or ""
                    is_fallback = False
                    if isinstance(tags_raw, list):
                        is_fallback = any(str(t).lower() == "fallback" for t in tags_raw)
                    elif isinstance(tags_raw, str):
                        if tags_raw.startswith("["):
                            try:
                                t_list = json.loads(tags_raw)
                                is_fallback = any(str(t).lower() == "fallback" for t in t_list)
                            except Exception:
                                is_fallback = "fallback" in tags_raw.lower()
                        else:
                            is_fallback = "fallback" in tags_raw.lower()
                    if is_fallback and content_len > 2000:
                        self.logger.log_system("⚠️ 检测到知识库结构异常（单条过长），触发自动修复重置...")
                        need_reload = True
                if db_items and not need_reload:
                    for it in db_items:
                        if isinstance(it.get("tags"), str):
                            try:
                                it["tags"] = json.loads(it["tags"])
                            except:
                                it["tags"] = [t.strip() for t in it["tags"].split(",") if t.strip()]
                    items.extend(db_items)
                    self.logger.log_system(f"📚 从数据库加载了 {len(items)} 条知识库条目")

            # 1. 执行重置
            if need_reload:
                self.logger.log_system("🔄 执行知识库重置 (KB_REFRESH/AutoFix)...")
                self.db.execute_update("DELETE FROM knowledge_base WHERE tenant_id = ?", (self.tenant_id,))
                items = [] # 确保为空，触发下方导入逻辑
                if kb_refresh:
                    self.cfg.set_kb_refresh_off()

            # 2. 如果数据库为空（或已重置），执行导入
            if not items:
                self._import_from_files(items)
                
        except Exception as e:
            self.logger.log_system(f"⚠️ 加载知识库失败: {e}")
            
        return items

    def _import_from_files(self, items):
        ts = datetime.now().isoformat()
        
        # 1. Knowledge Base.txt
        kb_text_file = self.cfg.get_platform_path("Knowledge Base.txt")
        if os.path.exists(kb_text_file):
            try:
                with open(kb_text_file, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                
                if content.strip():
                    self.logger.log_system("📂 正在解析并导入本地知识库...")
                    blocks = self._parse_multi_lang_qa(content)
                    md_blocks = []
                    if not blocks:
                        md_blocks = self._parse_markdown_kb(content)
                    
                    count = 0
                    if blocks:
                        for b in blocks:
                            full_content = f"Question: {b.get('q_sc','')}\nQuestion_TC: {b.get('q_tc','')}\nAnswer: {b.get('a_sc','')}\nAnswer_TC: {b.get('a_tc','')}"
                            new_item = self._create_item(b.get('q_sc', '')[:100] or "无标题QA", "qa", ["telegram", "kb", "parsed"], full_content, "Knowledge Base.txt", ts)
                            self.db.add_kb_item(new_item)
                            items.append(new_item)
                            count += 1
                        self.logger.log_system(f"✅ 成功导入 {count} 条 QA 知识库条目！")
                    elif md_blocks:
                        self.logger.log_system("⚠️ QA解析为空，采用 Markdown 标题分割导入...")
                        for mb in md_blocks:
                            new_item = self._create_item(mb['title'][:100], "markdown", ["telegram", "kb", "markdown"], mb['content'], "Knowledge Base.txt", ts)
                            self.db.add_kb_item(new_item)
                            items.append(new_item)
                            count += 1
                        self.logger.log_system(f"✅ 成功导入 {count} 条 Markdown 知识库条目！")
                    else:
                         # Fallback
                         self.logger.log_system("⚠️ 解析结果为空，执行整本导入(Fallback)...")
                         new_item = self._create_item("默认知识库 (Fallback)", "text", ["telegram", "kb", "fallback"], content, "Knowledge Base.txt", ts)
                         self.db.add_kb_item(new_item)
                         items.append(new_item)
            except Exception as e:
                self.logger.log_system(f"❌ 初始化导入失败: {e}")

        # 2. qa.txt
        qa_file = self.cfg.get_platform_path("qa.txt")
        if os.path.exists(qa_file):
            try:
                with open(qa_file, "r", encoding="utf-8") as f: qa_content = f.read()
                if qa_content.strip():
                    self.logger.log_system("📂 正在解析并导入 qa.txt (补充知识库)...")
                    qa_blocks = self._parse_multi_lang_qa(qa_content)
                    if qa_blocks:
                        count = 0
                        for b in qa_blocks:
                            full_content = f"Question: {b.get('q_sc','')}\nQuestion_TC: {b.get('q_tc','')}\nAnswer: {b.get('a_sc','')}\nAnswer_TC: {b.get('a_tc','')}"
                            new_item = self._create_item(b.get('q_sc', '')[:100] or "QA Pair", "qa_txt", ["telegram", "kb", "qa_txt"], full_content, "qa.txt", ts)
                            self.db.add_kb_item(new_item)
                            items.append(new_item)
                            count += 1
                        self.logger.log_system(f"✅ 成功从 qa.txt 导入 {count} 条知识库条目！")
            except Exception as e:
                self.logger.log_system(f"⚠️ 导入 qa.txt 失败: {e}")

        # 3. extra_kb.txt
        extra_file = self.cfg.get_platform_path("extra_kb.txt")
        if os.path.exists(extra_file):
            try:
                with open(extra_file, "r", encoding="utf-8") as f: extra_content = f.read()
                if extra_content.strip():
                    self.logger.log_system("📂 正在解析并导入 extra_kb.txt (额外知识库)...")
                    extra_blocks = self._parse_markdown_kb(extra_content)
                    if extra_blocks:
                        count = 0
                        for mb in extra_blocks:
                            new_item = self._create_item(mb['title'][:100], "markdown", ["telegram", "kb", "extra"], mb['content'], "extra_kb.txt", ts)
                            self.db.add_kb_item(new_item)
                            items.append(new_item)
                            count += 1
                        self.logger.log_system(f"✅ 成功从 extra_kb.txt 导入 {count} 条 Markdown 知识库条目！")
                    else:
                         self.logger.log_system("⚠️ extra_kb.txt 解析结果为空，执行整本导入...")
                         new_item = self._create_item("额外知识库 (Full)", "text", ["telegram", "kb", "extra", "fallback"], extra_content, "extra_kb.txt", ts)
                         self.db.add_kb_item(new_item)
                         items.append(new_item)
            except Exception as e:
                self.logger.log_system(f"⚠️ 导入 extra_kb.txt 失败: {e}")

    def _create_item(self, title, category, tags, content, source_file, ts):
        return {
            "id": str(uuid.uuid4()),
            "tenant_id": self.tenant_id,
            "title": title,
            "category": category,
            "tags": json.dumps(tags, ensure_ascii=False),
            "content": content,
            "source_file": source_file,
            "created_at": ts,
            "updated_at": ts
        }

    def _parse_multi_lang_qa(self, content):
        blocks = []
        if not content: return blocks
        lines = content.splitlines()
        cur = {"q_sc":"", "q_tc":"", "a_sc":"", "a_tc":""}
        cur_key = None
        
        def flush():
            nonlocal cur
            if any(cur.values()):
                blocks.append({k: (v.strip()) for k, v in cur.items()})
            cur = {"q_sc":"", "q_tc":"", "a_sc":"", "a_tc":""}

        for raw in lines:
            line = (raw or "").strip()
            if not line: continue
            if line.startswith("====="): continue
            if line.startswith("QA-"):
                flush()
                cur_key = None
                continue
            
            # Simple parsing logic
            for key, marker in [("q_sc", "【问题-简体】"), ("q_tc", "【问题-繁体】"), ("a_sc", "【答案-简体】"), ("a_tc", "【答案-繁体】")]:
                if line.startswith(marker):
                    cur_key = key
                    cur[cur_key] += line.replace(marker, "").strip()
                    break
            else:
                if cur_key:
                    cur[cur_key] += ("\n" + line)
        flush()
        return [b for b in blocks if any(b.values())]

    def _parse_markdown_kb(self, content):
        lines = content.splitlines()
        blocks = []
        current_title = "General"
        current_content = []
        
        for line in lines:
            if line.strip().startswith('#'):
                if current_content:
                    text = "\n".join(current_content).strip()
                    if text:
                        blocks.append({"title": current_title, "content": text})
                current_title = line.strip().lstrip('#').strip()
                current_content = [line]
            else:
                current_content.append(line)
                
        if current_content:
            text = "\n".join(current_content).strip()
            if text:
                blocks.append({"title": current_title, "content": text})
        return blocks
