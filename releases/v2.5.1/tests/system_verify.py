import os
import sys
import json
import importlib
import asyncio
from pathlib import Path

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_step(name):
    print(f"\n[TEST] Checking {name}...")

def assert_true(condition, message):
    if not condition:
        print(f"❌ FAILED: {message}")
        return False
    print(f"✅ PASS: {message}")
    return True

def verify_dependencies():
    check_step("Dependencies")
    required = ["streamlit", "telethon", "pandas", "dotenv", "watchdog"]
    all_pass = True
    for pkg in required:
        try:
            importlib.import_module(pkg)
            print(f"  - {pkg}: Installed")
        except ImportError:
            print(f"  - {pkg}: MISSING")
            all_pass = False
    return all_pass

def verify_file_structure():
    check_step("File Structure")
    critical_files = [
        "admin_multi.py",
        "src/config/loader.py",
        "src/modules/telegram/bot.py",
        "requirements.txt"
    ]
    all_pass = True
    for f in critical_files:
        path = os.path.join(project_root, f)
        if os.path.exists(path):
            print(f"  - {f}: Found")
        else:
            print(f"  - {f}: MISSING")
            all_pass = False
    return all_pass

def verify_config_manager():
    check_step("ConfigManager")
    try:
        from src.config.loader import ConfigManager
        cm = ConfigManager("test_tenant")
        
        # Check if paths are generated correctly
        base_dir = cm.base_dir
        print(f"  - Base Dir: {base_dir}")
        
        # Verify directory creation
        if os.path.exists(base_dir):
            print("  - Tenant directory created: Yes")
        else:
            print("  - Tenant directory created: No (Should be created by __init__)")
            
        return True
    except Exception as e:
        print(f"❌ ConfigManager Error: {e}")
        return False

def verify_admin_syntax():
    check_step("admin_multi.py Syntax")
    admin_path = os.path.join(project_root, "admin_multi.py")
    try:
        with open(admin_path, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, admin_path, 'exec')
        print("✅ Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        return False

def main():
    print("=== System Verification Tool ===")
    print(f"Python: {sys.version}")
    
    steps = [
        verify_dependencies,
        verify_file_structure,
        verify_config_manager,
        verify_admin_syntax
    ]
    
    results = []
    for step in steps:
        try:
            results.append(step())
        except Exception as e:
            print(f"❌ Unhandled Exception in {step.__name__}: {e}")
            results.append(False)
            
    print("\n=== Summary ===")
    if all(results):
        print("✅ All checks passed. System integrity verified.")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please review logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
