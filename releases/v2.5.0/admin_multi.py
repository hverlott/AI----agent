import streamlit as st
import os
import sys

# Auto-redirect to v2.5.1
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is .../releases/v2.5.0
# Fix: Ensure we correctly navigate up from v2.5.0 to releases then down to v2.5.1
# Using resolve() to handle potential symlinks or relative path weirdness
target_dir = os.path.abspath(os.path.join(current_dir, "..", "v2.5.1"))

# Fallback mechanism if the path construction fails (e.g., recursive calls)
if "releases" in current_dir and "v2.5.1" in current_dir:
     # We are already in v2.5.1 but running v2.5.0 script? 
     # This shouldn't happen with correct logic, but let's be safe.
     target_dir = current_dir

if not os.path.exists(target_dir):
    # Try absolute path assumption based on project root
    # Assumption: script is running in project_root/releases/v2.5.0/admin_multi.py
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    target_dir = os.path.join(project_root, "releases", "v2.5.1")
    
if not os.path.exists(target_dir):
    st.error(f"Critical Error: Target version directory not found: {target_dir}")
    st.stop()

target_file = os.path.join(target_dir, "admin_multi.py")

# Redirect setup
if target_dir not in sys.path:
    sys.path.insert(0, target_dir)
os.chdir(target_dir)

# Read and execute v2.5.1
try:
    with open(target_file, encoding='utf-8') as f:
        code = f.read()
    
    # Update globals to make the script think it's running from the new location
    global_vars = globals().copy()
    global_vars['__file__'] = target_file
    
    exec(code, global_vars)
except Exception as e:
    st.error(f"Failed to load v2.5.1: {e}")
