import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.environ.get("SAAS_DATA_DIR", "data")
            db_path = os.path.join(data_dir, "core.db")
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_schema()
        self._migrate_tables()

    def _ensure_db_dir(self):
        dirname = os.path.dirname(self.db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_schema(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # IP白名单 (V2.4.0 Security)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL, -- 'super_admin', 'business_admin'
            tenant_id TEXT,
            status TEXT DEFAULT 'active',
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ip_whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 登录日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 租户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            config TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')

        # 审计日志表 (替代 admin_ops.log)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            user_role TEXT,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 消息流水表 (用于高级分析)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            platform TEXT,
            chat_id TEXT,
            direction TEXT, -- 'in' or 'out'
            message_type TEXT, -- 'text', 'image', etc.
            status TEXT, -- 'success', 'failed', 'filtered'
            tokens_used INTEGER DEFAULT 0,
            model TEXT,
            cost REAL DEFAULT 0.0,
            stage TEXT,
            user_content TEXT,
            bot_response TEXT,
            is_junk INTEGER DEFAULT 0,
            is_learnable INTEGER DEFAULT 0,
            learning_ai_id TEXT,
            learning_tags TEXT,
            reviewed_at TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 每日统计聚合表 (加速查询)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE,
            tenant_id TEXT,
            metric_name TEXT,
            metric_value REAL,
            UNIQUE(date, tenant_id, metric_name)
        )
        ''')

        # 知识库表 (替代 db.json)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            title TEXT,
            category TEXT,
            tags TEXT,
            content TEXT,
            source_file TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            platform TEXT,
            user_id TEXT,
            current_stage TEXT,
            persona_id TEXT,
            intent_score REAL,
            risk_level TEXT,
            slots_json TEXT,
            handoff_required INTEGER,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(tenant_id, platform, user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS script_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            profile_type TEXT,
            name TEXT,
            version TEXT,
            content TEXT,
            enabled INTEGER,
            created_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS routing_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            platform TEXT,
            user_id TEXT,
            decision_json TEXT,
            created_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS upgrade_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_from TEXT,
            version_to TEXT,
            status TEXT,
            backup_path TEXT,
            details TEXT,
            started_at TEXT,
            finished_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            name TEXT,
            description TEXT,
            enabled INTEGER DEFAULT 0,
            bound_ai_id TEXT,
            config_json TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        conn.commit()
        conn.close()

    def _migrate_tables(self):
        """检查并迁移旧表结构"""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            # 检查 message_events 表是否缺少 model, cost, stage 字段
            cursor.execute("PRAGMA table_info(message_events)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'model' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN model TEXT")
            
            if 'cost' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN cost REAL DEFAULT 0.0")
            
            if 'stage' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN stage TEXT")
            
            if 'user_content' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN user_content TEXT")
                
            if 'bot_response' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN bot_response TEXT")
            
            if 'is_junk' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN is_junk INTEGER DEFAULT 0")
            
            if 'is_learnable' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN is_learnable INTEGER DEFAULT 0")
            
            if 'learning_ai_id' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN learning_ai_id TEXT")
            
            if 'learning_tags' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN learning_tags TEXT")
            
            if 'reviewed_at' not in columns:
                cursor.execute("ALTER TABLE message_events ADD COLUMN reviewed_at TEXT")

            # 检查 conversation_states 表是否缺少 risk_level, slots_json, handoff_required
            cursor.execute("PRAGMA table_info(conversation_states)")
            cs_columns = [info[1] for info in cursor.fetchall()]
            
            if 'risk_level' not in cs_columns:
                cursor.execute("ALTER TABLE conversation_states ADD COLUMN risk_level TEXT")
            
            if 'slots_json' not in cs_columns:
                cursor.execute("ALTER TABLE conversation_states ADD COLUMN slots_json TEXT")
                
            if 'handoff_required' not in cs_columns:
                cursor.execute("ALTER TABLE conversation_states ADD COLUMN handoff_required INTEGER DEFAULT 0")
                
            conn.commit()
        except Exception as e:
            print(f"Migration failed: {e}")
        finally:
            conn.close()

    # --- Generic Operations ---

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    # --- Business Specific ---

    def log_audit(self, tenant_id: str, role: str, action: str, details: Dict):
        self.execute_update(
            "INSERT INTO audit_logs (tenant_id, user_role, action, details) VALUES (?, ?, ?, ?)",
            (tenant_id, role, action, json.dumps(details, ensure_ascii=False))
        )

    def get_audit_logs(self, tenant_id: str = None, limit: int = 50) -> List[Dict]:
        query = "SELECT * FROM audit_logs"
        params = []
        if tenant_id:
            query += " WHERE tenant_id = ?"
            params.append(tenant_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        return self.execute_query(query, tuple(params))

    def record_message_event(self, tenant_id: str, platform: str, chat_id: str, direction: str, status: str, tokens_used: int = 0, model: str = None, cost: float = 0.0, stage: str = None, user_content: str = None, bot_response: str = None):
        self.execute_update(
            "INSERT INTO message_events (tenant_id, platform, chat_id, direction, status, tokens_used, model, cost, stage, user_content, bot_response) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tenant_id, platform, chat_id, direction, status, tokens_used, model, cost, stage, user_content, bot_response)
        )

    def list_message_events(
        self,
        tenant_id: str,
        platform: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        is_junk: Optional[int] = None,
        is_learnable: Optional[int] = None,
        learning_ai_id: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict]:
        wheres = ["tenant_id = ?"]
        params: List[Any] = [tenant_id]
        if platform and platform != "all":
            wheres.append("platform = ?")
            params.append(platform)
        if direction and direction != "all":
            wheres.append("direction = ?")
            params.append(direction)
        if status and status != "all":
            wheres.append("status = ?")
            params.append(status)
        if is_junk in (0, 1):
            wheres.append("is_junk = ?")
            params.append(int(is_junk))
        if is_learnable in (0, 1):
            wheres.append("is_learnable = ?")
            params.append(int(is_learnable))
        if learning_ai_id and learning_ai_id != "all":
            wheres.append("learning_ai_id = ?")
            params.append(learning_ai_id)
        if keyword:
            wheres.append("(user_content LIKE ? OR bot_response LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])
        query = f"""
        SELECT *
        FROM message_events
        WHERE {" AND ".join(wheres)}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """
        params.extend([int(limit), int(offset)])
        return self.execute_query(query, tuple(params))

    def update_message_learning_flags(
        self,
        ids: List[int],
        is_junk: Optional[int] = None,
        is_learnable: Optional[int] = None,
        learning_ai_id: Optional[str] = None,
        learning_tags: Optional[str] = None,
    ) -> int:
        if not ids:
            return 0
        fields = []
        params: List[Any] = []
        if is_junk in (0, 1):
            fields.append("is_junk = ?")
            params.append(int(is_junk))
        if is_learnable in (0, 1):
            fields.append("is_learnable = ?")
            params.append(int(is_learnable))
        if learning_ai_id is not None:
            fields.append("learning_ai_id = ?")
            params.append(learning_ai_id)
        if learning_tags is not None:
            fields.append("learning_tags = ?")
            params.append(learning_tags)
        fields.append("reviewed_at = ?")
        params.append(datetime.now().isoformat())
        if not fields:
            return 0
        placeholders = ",".join(["?"] * len(ids))
        query = f"UPDATE message_events SET {', '.join(fields)} WHERE id IN ({placeholders})"
        params.extend([int(x) for x in ids])
        return self.execute_update(query, tuple(params))

    def delete_message_events(self, ids: List[int]) -> int:
        if not ids:
            return 0
        placeholders = ",".join(["?"] * len(ids))
        query = f"DELETE FROM message_events WHERE id IN ({placeholders})"
        return self.execute_update(query, tuple([int(x) for x in ids]))

    def get_learning_counts(self, tenant_id: str) -> Dict[str, int]:
        rows = self.execute_query(
            """
            SELECT
              sum(case when is_junk = 1 then 1 else 0 end) as junk_count,
              sum(case when is_learnable = 1 then 1 else 0 end) as learnable_count,
              count(*) as total_count
            FROM message_events
            WHERE tenant_id = ?
            """,
            (tenant_id,),
        )
        if not rows:
            return {"total": 0, "junk": 0, "learnable": 0}
        r = rows[0]
        return {
            "total": int(r.get("total_count") or 0),
            "junk": int(r.get("junk_count") or 0),
            "learnable": int(r.get("learnable_count") or 0),
        }

    def upsert_skill(self, tenant_id: str, skill: Dict[str, Any]) -> str:
        skill_id = skill.get("id") or ""
        if not skill_id:
            skill_id = f"skill_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        now = datetime.now().isoformat()
        existing = self.execute_query(
            "SELECT id FROM skills WHERE id = ? AND tenant_id = ?",
            (skill_id, tenant_id),
        )
        payload = {
            "id": skill_id,
            "tenant_id": tenant_id,
            "name": skill.get("name") or "",
            "description": skill.get("description") or "",
            "enabled": 1 if bool(skill.get("enabled", False)) else 0,
            "bound_ai_id": skill.get("bound_ai_id") or "",
            "config_json": json.dumps(skill.get("config") or {}, ensure_ascii=False),
            "updated_at": now,
        }
        if existing:
            self.execute_update(
                "UPDATE skills SET name = ?, description = ?, enabled = ?, bound_ai_id = ?, config_json = ?, updated_at = ? WHERE id = ? AND tenant_id = ?",
                (
                    payload["name"],
                    payload["description"],
                    payload["enabled"],
                    payload["bound_ai_id"],
                    payload["config_json"],
                    payload["updated_at"],
                    skill_id,
                    tenant_id,
                ),
            )
        else:
            payload["created_at"] = now
            self.execute_update(
                "INSERT INTO skills (id, tenant_id, name, description, enabled, bound_ai_id, config_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payload["id"],
                    payload["tenant_id"],
                    payload["name"],
                    payload["description"],
                    payload["enabled"],
                    payload["bound_ai_id"],
                    payload["config_json"],
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
        return skill_id

    def list_skills(self, tenant_id: str) -> List[Dict[str, Any]]:
        rows = self.execute_query(
            "SELECT * FROM skills WHERE tenant_id = ? ORDER BY updated_at DESC",
            (tenant_id,),
        )
        result = []
        for r in rows:
            cfg = {}
            try:
                if r.get("config_json"):
                    cfg = json.loads(r["config_json"])
            except Exception:
                cfg = {}
            item = dict(r)
            item["config"] = cfg
            result.append(item)
        return result

    def delete_skill(self, tenant_id: str, skill_id: str) -> int:
        return self.execute_update(
            "DELETE FROM skills WHERE tenant_id = ? AND id = ?",
            (tenant_id, skill_id),
        )

    def get_tenant_config(self, tenant_id: str) -> Dict:
        rows = self.execute_query("SELECT config FROM tenants WHERE id = ?", (tenant_id,))
        if rows and rows[0]['config']:
            return json.loads(rows[0]['config'])
        return {}

    def upsert_tenant_config(self, tenant_id: str, config: Dict):
        existing = self.execute_query("SELECT id FROM tenants WHERE id = ?", (tenant_id,))
        now = datetime.now().isoformat()
        config_str = json.dumps(config, ensure_ascii=False)
        
        if existing:
            self.execute_update(
                "UPDATE tenants SET config = ?, updated_at = ? WHERE id = ?",
                (config_str, now, tenant_id)
            )
        else:
            self.execute_update(
                "INSERT INTO tenants (id, config, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (tenant_id, config_str, now, now)
            )

    def get_dashboard_metrics(self, tenant_id: str, days: int = 7) -> Dict:
        """获取聚合的商业数据"""
        # 1. Message Count Trend
        query = f"""
        SELECT date(timestamp) as day, count(*) as count 
        FROM message_events 
        WHERE tenant_id = ? AND timestamp >= date('now', '-{days} days')
        GROUP BY day ORDER BY day
        """
        rows = self.execute_query(query, (tenant_id,))
        msg_trend = {row['day']: row['count'] for row in rows}
        
        # 2. Token Usage & Cost & Active Users
        query_usage = f"""
        SELECT sum(tokens_used) as total_tokens, sum(cost) as total_cost, count(distinct chat_id) as active_users
        FROM message_events
        WHERE tenant_id = ? AND timestamp >= date('now', '-{days} days')
        """
        rows_usage = self.execute_query(query_usage, (tenant_id,))
        total_tokens = rows_usage[0]['total_tokens'] or 0
        total_cost = rows_usage[0]['total_cost'] or 0.0
        active_users = rows_usage[0]['active_users'] or 0
        
        # 3. Cost by Stage
        query_stage = f"""
        SELECT stage, sum(cost) as stage_cost
        FROM message_events
        WHERE tenant_id = ? AND timestamp >= date('now', '-{days} days')
        GROUP BY stage
        """
        rows_stage = self.execute_query(query_stage, (tenant_id,))
        cost_by_stage = {row['stage'] or 'Unknown': row['stage_cost'] for row in rows_stage}

        return {
            "message_trend": msg_trend,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "active_users": active_users,
            "cost_by_stage": cost_by_stage
        }

    # --- Knowledge Base Operations ---

    def get_kb_items(self, tenant_id: str) -> List[Dict]:
        query = "SELECT * FROM knowledge_base WHERE tenant_id = ? ORDER BY updated_at DESC"
        rows = self.execute_query(query, (tenant_id,))
        # Parse tags from JSON/String if needed, assuming simple string for now or comma-separated
        return rows

    def get_enabled_skills(self, tenant_id: str, bound_ai_id: str = None) -> List[Dict]:
        """
        获取启用的技能列表
        :param tenant_id: 租户ID
        :param bound_ai_id: 绑定的AI业务线ID (provider-model)，如果不传则只返回未绑定的通用技能(如果有此逻辑)，
                            或者这里我们假设必须匹配。
                            策略：返回 bound_ai_id 匹配的 + bound_ai_id 为空/null的(通用技能)
        """
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        sql = "SELECT * FROM skills WHERE tenant_id = ? AND enabled = 1"
        params = [tenant_id]
        
        if bound_ai_id:
            # 匹配指定AI 或 通用(NULL/Empty)
            sql += " AND (bound_ai_id = ? OR bound_ai_id IS NULL OR bound_ai_id = '')"
            params.append(bound_ai_id)
        else:
            # 如果没传AI ID，可能只返回通用的？或者返回所有启用的？
            # 按照 "匹配不同的ai业务线" 逻辑，没传ID可能意味着默认环境
            # 暂时只返回通用的
            sql += " AND (bound_ai_id IS NULL OR bound_ai_id = '')"
            
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        skills = []
        for row in rows:
            skills.append(dict(row))
        return skills

    def add_kb_item(self, item: Dict):
        query = """
        INSERT INTO knowledge_base (id, tenant_id, title, category, tags, content, source_file, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_update(query, (
            item['id'], item['tenant_id'], item['title'], item['category'], 
            item['tags'], item['content'], item['source_file'], 
            item['created_at'], item['updated_at']
        ))

    def update_kb_item(self, item_id: str, updates: Dict):
        # Construct dynamic update query
        fields = []
        values = []
        for k, v in updates.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(item_id)
        
        query = f"UPDATE knowledge_base SET {', '.join(fields)} WHERE id = ?"
        self.execute_update(query, tuple(values))

    def delete_kb_item(self, item_id: str):
        self.execute_update("DELETE FROM knowledge_base WHERE id = ?", (item_id,))

    def delete_conversation_state(self, tenant_id: str, platform: str, user_id: str):
        self.execute_update(
            "DELETE FROM conversation_states WHERE tenant_id = ? AND platform = ? AND user_id = ?",
            (tenant_id, platform, user_id)
        )

    def upsert_conversation_state(self, tenant_id: str, platform: str, user_id: str, state: Dict):
        existing = self.execute_query(
            "SELECT id FROM conversation_states WHERE tenant_id = ? AND platform = ? AND user_id = ?",
            (tenant_id, platform, user_id)
        )
        now = datetime.now().isoformat()
        slots_json = json.dumps(state.get("slots", {}), ensure_ascii=False)
        if existing:
            self.execute_update(
                "UPDATE conversation_states SET current_stage = ?, persona_id = ?, intent_score = ?, risk_level = ?, slots_json = ?, handoff_required = ?, updated_at = ? WHERE tenant_id = ? AND platform = ? AND user_id = ?",
                (
                    state.get("current_stage"), state.get("persona_id"), float(state.get("intent_score", 0.0)),
                    state.get("risk_level", "unknown"), slots_json, 1 if state.get("handoff_required") else 0,
                    now, tenant_id, platform, user_id
                )
            )
        else:
            self.execute_update(
                "INSERT INTO conversation_states (tenant_id, platform, user_id, current_stage, persona_id, intent_score, risk_level, slots_json, handoff_required, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    tenant_id, platform, user_id, state.get("current_stage"), state.get("persona_id"),
                    float(state.get("intent_score", 0.0)), state.get("risk_level", "unknown"), slots_json,
                    1 if state.get("handoff_required") else 0, now, now
                )
            )
    
    def get_conversation_state(self, tenant_id: str, platform: str, user_id: str) -> Dict:
        rows = self.execute_query(
            "SELECT * FROM conversation_states WHERE tenant_id = ? AND platform = ? AND user_id = ?",
            (tenant_id, platform, user_id)
        )
        if not rows:
            return {}
        row = rows[0]
        slots = {}
        try:
            if row.get("slots_json"):
                slots = json.loads(row["slots_json"])
        except:
            slots = {}
        return {
            "user_id": row.get("user_id"),
            "platform": row.get("platform"),
            "current_stage": row.get("current_stage"),
            "persona_id": row.get("persona_id"),
            "intent_score": float(row.get("intent_score") or 0.0),
            "risk_level": row.get("risk_level") or "unknown",
            "slots": slots,
            "handoff_required": bool(row.get("handoff_required")),
            "updated_at": row.get("updated_at")
        }
    
    def list_conversation_states(self, tenant_id: str, limit: int = 50) -> List[Dict]:
        rows = self.execute_query(
            "SELECT * FROM conversation_states WHERE tenant_id = ? ORDER BY updated_at DESC LIMIT ?",
            (tenant_id, limit)
        )
        result = []
        for r in rows:
            slots = {}
            try:
                if r.get("slots_json"):
                    slots = json.loads(r["slots_json"])
            except:
                slots = {}
            result.append({
                "user_id": r.get("user_id"),
                "platform": r.get("platform"),
                "current_stage": r.get("current_stage"),
                "persona_id": r.get("persona_id"),
                "intent_score": float(r.get("intent_score") or 0.0),
                "risk_level": r.get("risk_level") or "unknown",
                "slots": slots,
                "handoff_required": bool(r.get("handoff_required")),
                "updated_at": r.get("updated_at")
            })
        return result

    # --- Tenant & User Management (SaaS) ---

    def create_tenant(self, tenant_id: str, plan: str = "free"):
        self.execute_update(
            "INSERT INTO tenants (id, plan, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (tenant_id, plan, datetime.now(), datetime.now())
        )

    def list_tenants(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM tenants")
        
    def delete_tenant(self, tenant_id: str):
        self.execute_update("DELETE FROM tenants WHERE id = ?", (tenant_id,))

    def create_user(self, username: str, password_hash: str, role: str, tenant_id: str = None) -> int:
        return self.execute_update(
            "INSERT INTO users (username, password_hash, role, tenant_id, status) VALUES (?, ?, ?, ?, 'active')",
            (username, password_hash, role, tenant_id)
        )

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        rows = self.execute_query("SELECT * FROM users WHERE username = ?", (username,))
        return dict(rows[0]) if rows else None

    def list_users(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM users")

    def update_user_login(self, user_id: int):
        self.execute_update(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(), user_id)
        )

    # --- Security & Logs ---

    def list_ip_whitelist(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM ip_whitelist ORDER BY created_at DESC")

    def add_ip_whitelist(self, ip_address: str, description: str):
        self.execute_update(
            "INSERT INTO ip_whitelist (ip_address, description) VALUES (?, ?)",
            (ip_address, description)
        )
        
    def delete_ip_whitelist(self, id: int):
        self.execute_update("DELETE FROM ip_whitelist WHERE id = ?", (id,))

    def check_ip_whitelist(self, ip_address: str) -> bool:
        rows = self.execute_query(
            "SELECT id FROM ip_whitelist WHERE ip_address = ? AND is_active = 1", 
            (ip_address,)
        )
        return len(rows) > 0

    def record_login_history(self, user_id: int, username: str, ip: str, status: str):
        self.execute_update(
            "INSERT INTO login_history (user_id, username, ip_address, status) VALUES (?, ?, ?, ?)",
            (user_id, username, ip, status)
        )

    def get_login_history(self, limit: int = 100) -> List[Dict]:
        return self.execute_query(
            "SELECT * FROM login_history ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
    
    def upsert_script_profile(self, tenant_id: str, profile_type: str, name: str, version: str, content: str, enabled: bool = True):
        existing = self.execute_query(
            "SELECT id FROM script_profiles WHERE tenant_id = ? AND profile_type = ? AND name = ? AND version = ?",
            (tenant_id, profile_type, name, version)
        )
        now = datetime.now().isoformat()
        if existing:
            self.execute_update(
                "UPDATE script_profiles SET content = ?, enabled = ? WHERE id = ?",
                (content, 1 if enabled else 0, existing[0]["id"])
            )
        else:
            self.execute_update(
                "INSERT INTO script_profiles (tenant_id, profile_type, name, version, content, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tenant_id, profile_type, name, version, content, 1 if enabled else 0, now)
            )
    
    def get_script_profiles(self, tenant_id: str, profile_type: Optional[str] = None) -> List[Dict]:
        if profile_type:
            return self.execute_query(
                "SELECT * FROM script_profiles WHERE tenant_id = ? AND profile_type = ? AND enabled = 1",
                (tenant_id, profile_type)
            )
        return self.execute_query(
            "SELECT * FROM script_profiles WHERE tenant_id = ? AND enabled = 1",
            (tenant_id,)
        )
    
    def get_script_profile_by_name(self, tenant_id: str, profile_type: str, name: str, version: Optional[str] = None) -> Dict:
        if version:
            rows = self.execute_query(
                "SELECT * FROM script_profiles WHERE tenant_id = ? AND profile_type = ? AND name = ? AND version = ? AND enabled = 1",
                (tenant_id, profile_type, name, version)
            )
        else:
            rows = self.execute_query(
                "SELECT * FROM script_profiles WHERE tenant_id = ? AND profile_type = ? AND name = ? AND enabled = 1 ORDER BY id DESC",
                (tenant_id, profile_type, name)
            )
        return rows[0] if rows else {}
    
    def record_routing_decision(self, tenant_id: str, platform: str, user_id: str, decision_json: Dict):
        now = datetime.now().isoformat()
        self.execute_update(
            "INSERT INTO routing_decisions (tenant_id, platform, user_id, decision_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (tenant_id, platform, user_id, json.dumps(decision_json, ensure_ascii=False), now)
        )
    def get_routing_decisions(self, tenant_id: str, limit: int = 50) -> List[Dict]:
        rows = self.execute_query(
            "SELECT * FROM routing_decisions WHERE tenant_id = ? ORDER BY id DESC LIMIT ?",
            (tenant_id, limit)
        )
        result = []
        for r in rows:
            try:
                d = json.loads(r.get("decision_json") or "{}")
            except:
                d = {}
            result.append({
                "platform": r.get("platform"),
                "user_id": r.get("user_id"),
                "decision": d,
                "created_at": r.get("created_at")
            })
        return result
    
    def start_upgrade_log(self, version_from: str, version_to: str, backup_path: Optional[str] = None, details: Optional[Dict] = None) -> int:
        now = datetime.now().isoformat()
        return self.execute_update(
            "INSERT INTO upgrade_logs (version_from, version_to, status, backup_path, details, started_at) VALUES (?, ?, ?, ?, ?, ?)",
            (version_from, version_to, "running", backup_path or "", json.dumps(details or {}, ensure_ascii=False), now)
        )
    
    def finish_upgrade_log(self, log_id: int, status: str, details: Optional[Dict] = None):
        now = datetime.now().isoformat()
        self.execute_update(
            "UPDATE upgrade_logs SET status = ?, details = ?, finished_at = ? WHERE id = ?",
            (status, json.dumps(details or {}, ensure_ascii=False), now, log_id)
        )
    
    def list_upgrade_logs(self, limit: int = 100) -> List[Dict]:
        return self.execute_query(
            "SELECT * FROM upgrade_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    
    def cleanup_non_superadmin_roles(self) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM audit_logs WHERE user_role IS NOT NULL AND user_role <> ?", ("SuperAdmin",))
            affected = cursor.rowcount
            conn.commit()
            return affected or 0
        finally:
            conn.close()
    
    def backup_all(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_root = os.path.join(data_dir, "backups", f"backup-{ts}")
        os.makedirs(backup_root, exist_ok=True)
        src_db = os.path.join(base_dir, self.db_path) if not os.path.isabs(self.db_path) else self.db_path
        if os.path.exists(src_db):
            import shutil
            shutil.copy2(src_db, os.path.join(backup_root, "core.db"))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            import shutil
            shutil.copy2(env_path, os.path.join(backup_root, ".env"))
        user_sess = os.path.join(base_dir, "userbot_session.session")
        admin_sess = os.path.join(base_dir, "admin_session.session")
        import shutil
        if os.path.exists(user_sess):
            shutil.copy2(user_sess, os.path.join(backup_root, "userbot_session.session"))
        if os.path.exists(admin_sess):
            shutil.copy2(admin_sess, os.path.join(backup_root, "admin_session.session"))
        kb_dir = os.path.join(data_dir, "knowledge_base")
        if os.path.isdir(kb_dir):
            try:
                shutil.copytree(kb_dir, os.path.join(backup_root, "knowledge_base"), dirs_exist_ok=True)
            except Exception:
                pass
        return backup_root
    
    def restore_backup(self, backup_root: str) -> bool:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        src_db = os.path.join(backup_root, "core.db")
        env_path = os.path.join(backup_root, ".env")
        user_sess = os.path.join(backup_root, "userbot_session.session")
        admin_sess = os.path.join(backup_root, "admin_session.session")
        import shutil
        if os.path.exists(src_db):
            dst_db = os.path.join(base_dir, self.db_path) if not os.path.isabs(self.db_path) else self.db_path
            os.makedirs(os.path.dirname(dst_db), exist_ok=True)
            shutil.copy2(src_db, dst_db)
        if os.path.exists(env_path):
            shutil.copy2(env_path, os.path.join(base_dir, ".env"))
        if os.path.exists(user_sess):
            shutil.copy2(user_sess, os.path.join(base_dir, "userbot_session.session"))
        if os.path.exists(admin_sess):
            shutil.copy2(admin_sess, os.path.join(base_dir, "admin_session.session"))
        kb_src = os.path.join(backup_root, "knowledge_base")
        kb_dst = os.path.join(data_dir, "knowledge_base")
        if os.path.isdir(kb_src):
            try:
                os.makedirs(kb_dst, exist_ok=True)
                shutil.copytree(kb_src, kb_dst, dirs_exist_ok=True)
            except Exception:
                pass
        return True

    # --- Login History ---

    def record_login_history(self, user_id: int, username: str, ip: str = "unknown", status: str = "success"):
        self.execute_update(
            "INSERT INTO login_history (user_id, username, ip_address, status) VALUES (?, ?, ?, ?)",
            (user_id, username, ip, status)
        )

    def get_login_history(self, limit: int = 100) -> List[Dict]:
        return self.execute_query("SELECT * FROM login_history ORDER BY id DESC LIMIT ?", (limit,))

    # --- V2.4.0 User Management ---

# Global Instance
db = DatabaseManager()
