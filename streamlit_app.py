import os
import sys

# Calculate paths
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "releases", "v2.5.1")

# Add app dir to sys.path so imports work
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Change working directory to app dir so file reads (like data/) work relative to it
os.chdir(app_dir)

# Path to the actual Streamlit app
app_path = os.path.join(app_dir, "admin_multi.py")

# Execute the app file
# This allows the app to run within the Streamlit context initiated by this script
with open(app_path, encoding='utf-8') as f:
    code = f.read()
    
    # Update globals to make the script think it's running from the new location
    global_vars = globals().copy()
    global_vars['__file__'] = app_path

    exec(code, global_vars)
