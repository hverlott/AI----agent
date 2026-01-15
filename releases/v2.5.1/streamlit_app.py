import os
import sys

# Get the directory where this script is located (releases/v2.5.0)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add this directory to sys.path so imports work correctly
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Change working directory to ensure relative paths in the app work
os.chdir(current_dir)

# Path to the actual application file
app_path = os.path.join(current_dir, "admin_multi.py")

# Run the application
if os.path.exists(app_path):
    with open(app_path, encoding='utf-8') as f:
        code = f.read()
        exec(code, globals())
else:
    print(f"Error: Could not find {app_path}")
