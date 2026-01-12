import os
import sys

# Calculate paths
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "releases", "v2.5.0")

# Add app dir to sys.path so imports work
sys.path.insert(0, app_dir)

# Change working directory to app dir so file reads (like data/) work relative to it
os.chdir(app_dir)

# Path to the actual Streamlit app
app_path = os.path.join(app_dir, "admin_multi.py")

# Execute the app file
# This allows the app to run within the Streamlit context initiated by this script
with open(app_path, encoding='utf-8') as f:
    code = f.read()
    exec(code, globals())
