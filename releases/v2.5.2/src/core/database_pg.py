import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from .database import DatabaseManager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    from psycopg2.extensions import register_adapter
    register_adapter(dict, Json)
except ImportError:
    psycopg2 = None

class DatabaseManagerPG(DatabaseManager):
    def __init__(self, db_url: str = None):
        if not psycopg2:
            raise ImportError("psycopg2 is required for DatabaseManagerPG")
            
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            # Fallback to default local postgres
            self.db_url = "postgresql://postgres:postgres@localhost:5432/saas_ai"
        
        self.logger = logging.getLogger("DB_PG")
        # Ensure extension exists
        self._init_extensions()

    def _get_conn(self):
        return psycopg2.connect(self.db_url)

    def _init_extensions(self):
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.warning(f"Failed to init extensions: {e}")

    # --- Core Overrides ---

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Convert sqlite ? to %s
                pg_query = query.replace("?", "%s")
                cur.execute(pg_query, params)
                rows = cur.fetchall()
                # RealDictCursor returns dict-like objects
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Query failed: {e} | Query: {query}")
            return []
        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                pg_query = query.replace("?", "%s")
                cur.execute(pg_query, params)
                conn.commit()
                return cur.rowcount
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Update failed: {e} | Query: {query}")
            raise e
        finally:
            conn.close()

    # --- Method Overrides for Logic/Syntax Differences ---

    def create_user(self, username: str, password_hash: str, role: str, tenant_id: str = None) -> int:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash, role, tenant_id, status) VALUES (%s, %s, %s, %s, 'active') RETURNING id",
                    (username, password_hash, role, tenant_id)
                )
                conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Create user failed: {e}")
            return 0
        finally:
            conn.close()

    def upsert_tenant_config(self, tenant_id: str, config: Dict):
        # PG Upsert syntax
        query = """
        INSERT INTO tenants (id, config, created_at, updated_at) 
        VALUES (%s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE 
        SET config = EXCLUDED.config, updated_at = NOW()
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (tenant_id, json.dumps(config)))
            conn.commit()
        finally:
            conn.close()

    def get_tenant_config(self, tenant_id: str) -> Dict:
        # Override to handle PG JSONB automatic decoding
        rows = self.execute_query("SELECT config FROM tenants WHERE id = ?", (tenant_id,))
        if rows and rows[0]['config']:
            cfg = rows[0]['config']
            return cfg if isinstance(cfg, dict) else json.loads(cfg)
        return {}
        
    def set_system_config(self, key: str, value: str):
        # PG ON CONFLICT syntax
        self.execute_update(
            "INSERT INTO system_configs (key, value, updated_at) VALUES (?, ?, NOW()) ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()",
            (key, value)
        )

    def upsert_script_profile(self, tenant_id: str, profile_type: str, name: str, version: str, content: str, enabled: bool = True):
        # We can implement this with ON CONFLICT if we had a unique constraint on these 4 columns
        # schema.sql says: UNIQUE(tenant_id, profile_type, name, version)
        # So we can use ON CONFLICT
        query = """
        INSERT INTO script_profiles (tenant_id, profile_type, name, version, content, enabled, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (tenant_id, profile_type, name, version) 
        DO UPDATE SET content = EXCLUDED.content, enabled = EXCLUDED.enabled, updated_at = NOW()
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (
                    tenant_id, profile_type, name, version, content, 
                    1 if enabled else 0
                ))
            conn.commit()
        finally:
            conn.close()

    # --- RAG / Vector Operations (PG Specific) ---
    
    def upsert_kb_embedding(self, tenant_id: str, kb_id: int, embedding: List[float]):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_embeddings (tenant_id, kb_id, embedding) VALUES (%s, %s, %s)",
                    (tenant_id, kb_id, embedding)
                )
            conn.commit()
        finally:
            conn.close()

    def search_kb_vectors(self, tenant_id: str, query_vec: List[float], limit: int = 5):
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT k.*, 1 - (e.embedding <=> %s::vector) as similarity
                    FROM kb_embeddings e
                    JOIN knowledge_base k ON e.kb_id = k.id
                    WHERE e.tenant_id = %s
                    ORDER BY e.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_vec, tenant_id, query_vec, limit)
                )
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # --- Helper methods that might need overriding ---
    
    def list_message_events(self, tenant_id: str, **kwargs) -> List[Dict]:
        # Reuse parent logic but ensure boolean flags (0/1) are handled if needed.
        # SQLite uses 0/1 for booleans. PG can too if column is INTEGER.
        # schema.sql: is_junk INTEGER DEFAULT 0. So it matches.
        return super().list_message_events(tenant_id, **kwargs)

    # _migrate_tables is skipped because we use schema.sql for PG
    def _migrate_tables(self):
        # Even with PG, we might need to add indexes if schema.sql didn't have them originally
        # or if we are upgrading an existing DB.
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                # Add columns if missing (PG way)
                # For brevity, assuming schema is mostly stable or handled by external tools.
                # But let's add the indexes as requested for performance optimization.
                
                # Check if index exists is harder in PG without querying system catalogs.
                # simpler: "CREATE INDEX IF NOT EXISTS"
                cur.execute("CREATE INDEX IF NOT EXISTS idx_msg_tenant_time ON message_events(tenant_id, timestamp DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_msg_learning ON message_events(tenant_id, is_learnable, is_junk)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_msg_chat ON message_events(chat_id, timestamp)")
            conn.commit()
        except Exception as e:
            self.logger.warning(f"PG Migration (Indexes) warning: {e}")
        finally:
            conn.close()
    
    # _ensure_db_dir is skipped
    def _ensure_db_dir(self):
        pass

