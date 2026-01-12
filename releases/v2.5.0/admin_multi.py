import streamlit as st
import os
import sys

# Auto-redirect to v2.5.1
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is .../releases/v2.5.0
target_dir = os.path.abspath(os.path.join(current_dir, "..", "v2.5.1"))
# target_dir is .../releases/v2.5.1

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
