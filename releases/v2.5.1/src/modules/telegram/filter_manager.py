import os
import json
import re
import logging
from typing import List, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FilterManager:
    _mem_cache = {}

    def __init__(self, tenant_id: str = "default", project_root: str = None):
        self.tenant_id = tenant_id
        if project_root:
            self.root_dir = project_root
        else:
            # Assume we are in src/modules/telegram
            self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        
        self.cache_dir = os.path.join(self.root_dir, "cache", "filters")
        self.blacklist_file = os.path.join(self.cache_dir, f"nickname_blacklist_{self.tenant_id}.json")
        
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create filter cache directory: {e}")

    def load_blacklist(self) -> List[str]:
        """Load nickname blacklist patterns with caching."""
        if not os.path.exists(self.blacklist_file):
            return []
            
        try:
            mtime = os.path.getmtime(self.blacklist_file)
            cache_key = (self.tenant_id, self.root_dir)
            
            cached = self._mem_cache.get(cache_key)
            if cached and cached["mtime"] == mtime:
                return cached["patterns"]

            with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
                self._mem_cache[cache_key] = {"mtime": mtime, "patterns": patterns}
                return patterns
        except Exception as e:
            logger.error(f"Error loading blacklist: {e}")
            return []

    def save_blacklist(self, patterns: List[str]):
        """Save nickname blacklist patterns."""
        try:
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving blacklist: {e}")

    def is_blocked(self, display_name: str) -> bool:
        """Check if a display name is blocked by any pattern."""
        patterns = self.load_blacklist()
        if not patterns:
            return False
            
        for pattern in patterns:
            try:
                if re.search(pattern, display_name, re.IGNORECASE):
                    return True
            except re.error:
                logger.warning(f"Invalid regex pattern in blacklist: {pattern}")
                continue
        return False
