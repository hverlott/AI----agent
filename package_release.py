import os
import zipfile
import datetime

def zip_release(source_dir, output_filename, exclude_dirs=None, exclude_exts=None):
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_exts is None:
        exclude_exts = []
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                if file.startswith('.'): # Skip hidden files like .env
                    continue
                    
                file_path = os.path.join(root, file)
                # Calculate relative path for the zip entry
                arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                
                print(f"Adding {arcname}...")
                zipf.write(file_path, arcname)

if __name__ == "__main__":
    source_dir = r"d:\SaaS-AIs\releases\v2.5.1"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_zip = f"d:\\SaaS-AIs\\SaaS-AI-System-v2.5.1-Release-{timestamp}.zip"
    
    exclude_dirs = [
        "__pycache__", 
        "venv", 
        "venv313", 
        "logs", 
        "cache", 
        ".git", 
        ".idea", 
        ".vscode",
        "tests" # Optional: exclude tests in release build? Keeping tests for now as requested by some users, but maybe not unit tests. Let's keep tests.
    ]
    
    # Exclude specific heavy or sensitive extensions/files
    exclude_exts = [
        ".pyc", 
        ".pyd", 
        ".session", 
        ".session-journal", 
        ".log"
    ]
    
    print(f"Packaging release from {source_dir} to {output_zip}...")
    try:
        zip_release(source_dir, output_zip, exclude_dirs, exclude_exts)
        print(f"✅ Successfully packaged release: {output_zip}")
    except Exception as e:
        print(f"❌ Failed to package release: {e}")
