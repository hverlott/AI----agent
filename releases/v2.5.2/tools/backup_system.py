import os
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BACKUP_DIR = os.path.join(ROOT, "data", "backups")
INCLUDE_PATHS = [
    os.path.join(ROOT, "platforms"),
    os.path.join(ROOT, "data"),
    os.path.join(ROOT, "admin_multi.py"),
    os.path.join(ROOT, "admin.py"),
    os.path.join(ROOT, "audit_manager.py"),
    os.path.join(ROOT, "keyword_manager.py"),
    os.path.join(ROOT, ".env"),
]

def safe_copy(src, dst):
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        return True, ""
    except Exception as e:
        return False, str(e)

def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = os.path.join(BACKUP_DIR, f"backup-{ts}")
    os.makedirs(target, exist_ok=True)
    report = []
    for path in INCLUDE_PATHS:
        if not os.path.exists(path):
            report.append((path, "skip(not found)"))
            continue
        rel = os.path.relpath(path, ROOT)
        dst = os.path.join(target, rel)
        ok, err = safe_copy(path, dst)
        report.append((rel, "ok" if ok else f"error: {err}"))
    # write report
    with open(os.path.join(target, "backup_report.txt"), "w", encoding="utf-8") as f:
        for item, status in report:
            f.write(f"{item}: {status}\n")
    print(f"Backup completed: {target}")

if __name__ == "__main__":
    main()
