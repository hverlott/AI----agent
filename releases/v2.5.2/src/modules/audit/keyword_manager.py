import json
import os
import logging
from datetime import datetime

# Configure logger (write to audit.log for unified visibility)
logger = logging.getLogger("KeywordManager")
logger.setLevel(logging.INFO)
try:
    log_dir = os.path.join("platforms", "telegram", "logs")
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, "audit.log"), encoding="utf-8")
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(fh)
except Exception:
    pass

class KeywordManager:
    _global_state = {}
    _global_mtime = {}

    def __init__(self, config_path=None):
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.path.join("platforms", "telegram", "keywords.json")
        
        if self.config_path in KeywordManager._global_state:
            st = KeywordManager._global_state[self.config_path]
            self.keywords = st.get("keywords", {})
            self.last_mtime = st.get("mtime", 0)
        else:
            self.keywords = {}
            self.last_mtime = 0
        self._load()

    def _load(self):
        """Load keywords from file if modified"""
        try:
            if not os.path.exists(self.config_path):
                self.keywords = {
                    "block": [],      # Prohibited words, hard block
                    "sensitive": [], 
                    "allow": []
                }
                self._save()
                return

            mtime = os.path.getmtime(self.config_path)
            g_mtime = KeywordManager._global_mtime.get(self.config_path, 0)
            if mtime > max(self.last_mtime, g_mtime):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.keywords = json.load(f)
                self.last_mtime = mtime
                KeywordManager._global_state[self.config_path] = {"keywords": self.keywords, "mtime": mtime}
                KeywordManager._global_mtime[self.config_path] = mtime
                logger.info(f"Loaded keywords from {self.config_path}")
            else:
                if self.config_path in KeywordManager._global_state:
                    st = KeywordManager._global_state[self.config_path]
                    self.keywords = st.get("keywords", self.keywords)
                    self.last_mtime = st.get("mtime", self.last_mtime)
        except Exception as e:
            logger.error(f"Failed to load keywords: {e}")

    def _save(self):
        """Save keywords to file with transactional replace"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            tmp_path = self.config_path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.config_path)
            # Update mtime to prevent reloading own save
            self.last_mtime = os.path.getmtime(self.config_path)
            KeywordManager._global_state[self.config_path] = {"keywords": self.keywords, "mtime": self.last_mtime}
            KeywordManager._global_mtime[self.config_path] = self.last_mtime
            logger.info(f"KEYWORDS_SAVE path={self.config_path} total_block={len(self.keywords.get('block', []))} total_sensitive={len(self.keywords.get('sensitive', []))}")
        except Exception as e:
            logger.error(f"Failed to save keywords: {e}")

    def get_keywords(self):
        """Get all keywords"""
        self._load()
        return self.keywords

    def add_keyword(self, category, word):
        """Add a keyword to a category"""
        self._load()
        if category not in self.keywords:
            self.keywords[category] = []
        
        if word not in self.keywords[category]:
            self.keywords[category].append(word)
            self._save()
            logger.info(f"KEYWORD_ADD category={category} word={word}")
            return True, f"Added '{word}' to '{category}'"
        return False, f"'{word}' already exists in '{category}'"

    def remove_keyword(self, category, word):
        """Remove a keyword from a category"""
        self._load()
        if category in self.keywords and word in self.keywords[category]:
            self.keywords[category].remove(word)
            self._save()
            logger.info(f"KEYWORD_REMOVE category={category} word={word}")
            return True, f"Removed '{word}' from '{category}'"
        return False, f"'{word}' not found in '{category}'"

    def rename_keyword(self, category, old_word, new_word):
        """Rename a keyword within a category"""
        self._load()
        if category not in self.keywords:
            return False, f"Category '{category}' not found"
        items = self.keywords[category]
        try:
            idx = items.index(old_word)
        except ValueError:
            return False, f"'{old_word}' not found in '{category}'"
        if new_word in items:
            return False, f"'{new_word}' already exists in '{category}'"
        items[idx] = new_word
        self._save()
        logger.info(f"KEYWORD_RENAME category={category} old={old_word} new={new_word}")
        return True, f"Renamed '{old_word}' to '{new_word}' in '{category}'"
    def check_text(self, text):
        """
        Check text against keywords.
        Returns: (is_safe, category, matched_word)
        """
        self._load()
        # Allowlist precedence
        if 'allow' in self.keywords:
            for word in self.keywords['allow']:
                if word and word in text:
                    return True, 'allow', word
        # Check 'block' category (Hard Fail)
        if 'block' in self.keywords:
            for word in self.keywords['block']:
                if word in text:
                    return False, 'block', word
        
        # Check 'sensitive' category (Soft Fail / Warning - for now treated as Fail for safety)
        if 'sensitive' in self.keywords:
            for word in self.keywords['sensitive']:
                if word in text:
                    return False, 'sensitive', word
                    
        return True, None, None
