import os
import zipfile
import shutil
from pathlib import Path

def create_release_package():
    # Configuration
    VERSION = "v2.5.0"
    PACKAGE_NAME = f"SaaS-AI-System-{VERSION}"
    SOURCE_DIR = Path(__file__).parent.absolute()
    OUTPUT_ZIP = SOURCE_DIR / f"{PACKAGE_NAME}.zip"
    
    # Files and directories to include
    INCLUDES = [
        "admin_multi.py",
        "main.py",
        "src",
        "platforms",
        "requirements.txt",
        ".env.example",
        "config.txt",
        "prompt.txt",
        "README.md",
        "ADMIN_README.md",
        "DEPLOYMENT_GUIDE.md"
    ]
    
    # Excludes (patterns)
    EXCLUDES = [
        "__pycache__",
        "*.pyc",
        ".git",
        ".vscode",
        "tests", # Do we include tests? Maybe not for production deployment unless requested.
        "*.log",
        "*.session",
        "*.session-journal"
    ]

    print(f"📦 Packaging {PACKAGE_NAME}...")
    print(f"📍 Source: {SOURCE_DIR}")
    
    try:
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item_name in INCLUDES:
                item_path = SOURCE_DIR / item_name
                
                if not item_path.exists():
                    print(f"⚠️ Warning: {item_name} not found, skipping.")
                    continue
                
                if item_path.is_file():
                    print(f"  Adding file: {item_name}")
                    zf.write(item_path, arcname=item_name)
                
                elif item_path.is_dir():
                    print(f"  Adding directory: {item_name}")
                    for root, dirs, files in os.walk(item_path):
                        # Filter directories
                        dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith("__")]
                        
                        for file in files:
                            # Filter files
                            if any(file.endswith(ext.replace("*", "")) for ext in EXCLUDES if "*" in ext):
                                continue
                            if file in EXCLUDES:
                                continue
                                
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(SOURCE_DIR)
                            zf.write(file_path, arcname=arcname)
                            
        print(f"\n✅ Package created successfully!")
        print(f"📁 Location: {OUTPUT_ZIP}")
        print(f"📏 Size: {OUTPUT_ZIP.stat().st_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"\n❌ Error creating package: {e}")

if __name__ == "__main__":
    create_release_package()
