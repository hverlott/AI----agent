import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Set

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhitelistManager:
    def __init__(self, tenant_id: str = "default", project_root: str = None):
        self.tenant_id = tenant_id
        if project_root:
            self.root_dir = project_root
        else:
            # Assume we are in src/modules/telegram, go up 3 levels to project root (v2.5.1)
            # src/modules/telegram -> src/modules -> src -> v2.5.1
            self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        
        self.cache_dir = os.path.join(self.root_dir, "cache", "group_whitelist")
        self.cache_file = os.path.join(self.cache_dir, f"whitelist_{self.tenant_id}.json")
        
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                logger.info(f"Created whitelist cache directory: {self.cache_dir}")
            except Exception as e:
                logger.error(f"Failed to create cache directory {self.cache_dir}: {e}")

    def _init_empty_cache(self) -> Dict[str, Any]:
        """Initialize and save an empty cache structure."""
        empty_cache = {}
        self._save_cache(empty_cache)
        return empty_cache

    def _save_cache(self, data: Dict[str, Any]):
        """Save data to cache file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save whitelist cache to {self.cache_file}: {e}")
            raise

    def load_whitelist(self) -> Dict[str, Any]:
        """
        Load the whitelist cache.
        Returns a dict mapping group_id to {status, updated_at}.
        """
        if not os.path.exists(self.cache_file):
            logger.info(f"Whitelist cache not found at {self.cache_file}, initializing empty.")
            return self._init_empty_cache()
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError:
            logger.error(f"Corrupted whitelist cache at {self.cache_file}, re-initializing.")
            return self._init_empty_cache()
        except Exception as e:
            logger.error(f"Error loading whitelist cache: {e}")
            return {}

    def get_whitelist_ids(self) -> Set[str]:
        """Return a set of whitelisted group IDs (compatibility mode)."""
        data = self.load_whitelist()
        # Filter where status is True
        return {gid for gid, info in data.items() if info.get("status") is True}

    def update_whitelist(self, group_ids: List[str]):
        """
        Update the whitelist with the provided list of ACTIVE group IDs.
        Groups not in the list but in cache will be marked as status=False (or removed? 
        Requirement says 'status' field, so likely toggle).
        
        However, usually a multiselect returns ONLY the selected items.
        So we should set these to True, and others to False? 
        Or just store the selected ones?
        
        "Cache data needs to include group ID, whitelist status, and last update time"
        
        If we only store selected ones, status is always True. 
        If we store all seen groups, we need the full list of groups to know what's "unselected".
        
        Given the input is usually from a multiselect of ALL groups, 
        we will assume we only care about tracking the "True" ones for now, 
        but the data structure supports "False".
        
        To support "False", we would need the full list of groups passed in.
        For now, let's implement a bulk set that sets provided IDs to True, 
        and we might need to handle the "False" ones if we want to keep history.
        
        Strategy: 
        1. Load current cache.
        2. Set all currently True to False (reset).
        3. Set new IDs to True.
        4. Update timestamps.
        """
        current_cache = self.load_whitelist()
        
        # Mark all existing as False first (optional, depends on if we want to keep history)
        # If we just want to reflect the current selection, we can just clear and rebuild, 
        # OR we keep the record but set status=False.
        # Let's keep the record for history.
        
        now_str = datetime.now().isoformat()
        
        # 1. Set all to False
        for gid in current_cache:
            current_cache[gid]["status"] = False
            current_cache[gid]["updated_at"] = now_str
            
        # 2. Set new to True
        for gid in group_ids:
            gid_str = str(gid) # Ensure string
            if gid_str in current_cache:
                current_cache[gid_str]["status"] = True
                current_cache[gid_str]["updated_at"] = now_str
            else:
                current_cache[gid_str] = {
                    "id": gid_str,
                    "status": True,
                    "updated_at": now_str,
                    "config": {}
                }
            
        self._save_cache(current_cache)

    def get_group_config(self, group_id: str) -> Dict[str, Any]:
        """Get configuration for a specific group."""
        cache = self.load_whitelist()
        gid_str = str(group_id)
        if gid_str in cache:
            return cache[gid_str].get("config", {})
        return {}

    def update_group_config(self, group_id: str, config: Dict[str, Any]):
        """Update configuration for a specific group."""
        cache = self.load_whitelist()
        gid_str = str(group_id)
        
        if gid_str not in cache:
            # If not in cache, add it as disabled but with config? 
            # Or assume it must be added first? 
            # Let's add it with status=False if not present, or just fail?
            # Better to auto-add as status=False (known group)
            cache[gid_str] = {
                "id": gid_str,
                "status": False,
                "updated_at": datetime.now().isoformat(),
                "config": config
            }
        else:
            if "config" not in cache[gid_str]:
                cache[gid_str]["config"] = {}
            cache[gid_str]["config"].update(config)
            cache[gid_str]["updated_at"] = datetime.now().isoformat()
            
        self._save_cache(cache)

    def add_group(self, group_id: str):
        """Add a single group to whitelist."""
        cache = self.load_whitelist()
        cache[str(group_id)] = {
            "id": str(group_id),
            "status": True,
            "updated_at": datetime.now().isoformat()
        }
        self._save_cache(cache)

    def remove_group(self, group_id: str):
        """Remove (disable) a single group."""
        cache = self.load_whitelist()
        gid_str = str(group_id)
        if gid_str in cache:
            cache[gid_str]["status"] = False
            cache[gid_str]["updated_at"] = datetime.now().isoformat()
            self._save_cache(cache)
