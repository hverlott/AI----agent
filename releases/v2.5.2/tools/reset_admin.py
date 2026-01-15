import sys
import os

# Add project root to path (parent of tools dir)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.core.database import db
    from auth_core import AuthManager
except ImportError:
    # Fallback if running from root
    sys.path.append(os.getcwd())
    from src.core.database import db
    from auth_core import AuthManager

def reset_admin():
    auth = AuthManager(db)
    username = "admin"
    password = "admin123"
    
    print(f"Checking user: {username}")
    user = db.get_user_by_username(username)
    
    if user:
        print(f"User {username} exists (ID: {user['id']}). Updating password...")
        # Manually hash and update
        p_hash, salt = auth._hash_password(password)
        stored_pw = f"{salt}${p_hash}"
        
        # We need to execute a raw update query since db doesn't expose update_password
        db.execute_update(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (stored_pw, username)
        )
        print(f"✅ Password for '{username}' has been reset to '{password}'.")
    else:
        print(f"User {username} does not exist. Creating...")
        success, msg = auth.create_user(username, password, "super_admin", None)
        if success:
            print(f"✅ User '{username}' created with password '{password}'.")
        else:
            print(f"❌ Failed to create user: {msg}")

if __name__ == "__main__":
    reset_admin()
