import os
import sys
import json
import sqlite3
import shutil
from datetime import datetime

# Adjust path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.database import DatabaseManager

def migrate_file_configs(db):
    """
    Migrate file-based configurations (tenants, platforms) to Database.
    Target tables: tenants, skills, system_configs
    """
    print("🚀 Starting Migration: File Configs -> Database")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "data")
    tenants_dir = os.path.join(data_dir, "tenants")
    
    if not os.path.exists(tenants_dir):
        print(f"⚠️ Tenants directory not found: {tenants_dir}")
        return

    # Iterate over tenants
    for tenant_id in os.listdir(tenants_dir):
        tdir = os.path.join(tenants_dir, tenant_id)
        if not os.path.isdir(tdir):
            continue
            
        print(f"Processing tenant: {tenant_id}")
        
        # 1. Migrate Platform Configs (Telegram)
        tg_conf_path = os.path.join(tdir, "platforms", "telegram", "config.txt")
        if os.path.exists(tg_conf_path):
            try:
                conf_map = {}
                with open(tg_conf_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        conf_map[k.strip()] = v.strip()
                
                # Update Tenant Config in DB
                # First get existing config to merge? Or just overwrite?
                # The 'tenants' table has a 'config' column which is a JSON.
                # Let's see if we should store platform config there.
                # Usually 'tenants' table stores plan info.
                # But 'upsert_tenant_config' stores generic config.
                
                # Let's store it.
                db.upsert_tenant_config(tenant_id, conf_map)
                print(f"  ✅ Migrated Telegram config ({len(conf_map)} keys)")
                
            except Exception as e:
                print(f"  ❌ Failed to migrate Telegram config: {e}")

        # 2. Migrate Keywords (keywords.txt)
        kw_path = os.path.join(tdir, "platforms", "telegram", "keywords.txt")
        if os.path.exists(kw_path):
            # Maybe store in system_config or tenant config?
            # Or just keep as file? The prompt said "migrate ALL storage content".
            # For now, let's put it in tenant config under "keywords"
            try:
                kws = []
                with open(kw_path, "r", encoding="utf-8") as f:
                    kws = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                
                # Fetch current config, update, save
                curr = db.get_tenant_config(tenant_id)
                curr["keywords_list"] = kws
                db.upsert_tenant_config(tenant_id, curr)
                print(f"  ✅ Migrated {len(kws)} keywords")
            except Exception as e:
                print(f"  ❌ Failed to migrate keywords: {e}")

    print("🏁 Migration Completed.")

def init_db_structure():
    """
    Ensure DB structure is ready (Tables & Indexes).
    This is handled by DatabaseManager init, but we can explicitly call it.
    """
    print("🔧 Initializing Database Structure...")
    # Just instantiating DatabaseManager triggers _init_schema and _migrate_tables
    db = DatabaseManager() 
    # If PG, we might need env vars, but let's assume default or SQLite for local dev script
    return db

if __name__ == "__main__":
    db = init_db_structure()
    migrate_file_configs(db)
