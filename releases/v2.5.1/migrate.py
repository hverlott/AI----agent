import os
import shutil
import sys

SRC = r"D:\AI Talk"
DST = r"D:\SaaS-AIs"

IGNORE_PATTERNS = [
    ".venv", ".git", "__pycache__", ".idea", ".vscode", "node_modules",
    "d:\\SaaS-AIs", "SaaS-AIs" # Ensure we don't copy dest if it's inside src
]

IGNORE_EXTENSIONS = [
    ".log", ".pid", ".tmp", ".bak", ".spec", ".session"
]

def should_ignore(name):
    if name in IGNORE_PATTERNS:
        return True
    for pat in IGNORE_PATTERNS:
        if name.startswith(pat):
            return True
    for ext in IGNORE_EXTENSIONS:
        if name.endswith(ext):
            return True
    return False

def main():
    print(f"Migrating from {SRC} to {DST}...")
    
    if not os.path.exists(DST):
        os.makedirs(DST)
        print(f"Created {DST}")

    items = os.listdir(SRC)
    
    for item in items:
        if should_ignore(item):
            print(f"Skipping {item}")
            continue
            
        s = os.path.join(SRC, item)
        d = os.path.join(DST, item)
        
        # Avoid recursive copy of dest
        if os.path.abspath(s) == os.path.abspath(DST):
            continue

        try:
            if os.path.isdir(s):
                # Use shutil.copytree for directories, but with ignore patterns
                # We need to handle if dest exists (merge/overwrite)
                if os.path.exists(d):
                    # For simplicity in this script, we can remove and recopy or use dirs_exist_ok
                    # But copytree with dirs_exist_ok=True is available in Python 3.8+
                    print(f"Copying dir {item}...")
                    shutil.copytree(s, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.log', '*.pid', 'node_modules', '.venv*'))
                else:
                    print(f"Copying dir {item}...")
                    shutil.copytree(s, d, ignore=shutil.ignore_patterns('__pycache__', '*.log', '*.pid', 'node_modules', '.venv*'))
            else:
                print(f"Copying file {item}...")
                shutil.copy2(s, d)
        except Exception as e:
            print(f"Error copying {item}: {e}")

    print("Migration completed.")

if __name__ == "__main__":
    main()
