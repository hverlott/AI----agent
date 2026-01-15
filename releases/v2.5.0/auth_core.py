import hashlib
import os
from database import DatabaseManager

class AuthManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        if not salt:
            salt = os.urandom(16).hex()
        # Simple SHA256 with salt
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return key.hex(), salt

    def create_user(self, username, password, role, tenant_id=None):
        existing = self.db.get_user_by_username(username)
        if existing:
            return False, "Username already exists"
        
        p_hash, salt = self._hash_password(password)
        # Store as salt$hash
        stored_pw = f"{salt}${p_hash}"
        
        try:
            uid = self.db.create_user(username, stored_pw, role, tenant_id)
            return True, uid
        except Exception as e:
            return False, str(e)

    def login(self, username, password, ip_address="unknown"):
        user = self.db.get_user_by_username(username)
        if not user:
            return None
        
        if user.get('status') != 'active':
            self.db.record_login_history(user['id'], username, ip_address, "failed_inactive")
            return None

        stored_pw = user['password_hash']
        if '$' not in stored_pw:
            self.db.record_login_history(user['id'], username, ip_address, "failed_format")
            return None
            
        salt, p_hash = stored_pw.split('$')
        check_hash, _ = self._hash_password(password, salt)
        
        if check_hash == p_hash:
            self.db.update_user_login(user['id'])
            self.db.record_login_history(user['id'], username, ip_address, "success")
            return user
        else:
            self.db.record_login_history(user['id'], username, ip_address, "failed_password")
            return None
