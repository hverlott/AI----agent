import os
import re
from pathlib import Path
import shutil

class VersionManager:
    def __init__(self, base_dir=None):
        # Base dir is expected to be releases/vX.X.X/
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).resolve().parent

        # Assuming structure: root/releases/vX.X.X
        self.releases_dir = self.base_dir.parent
        self.root_dir = self.releases_dir.parent
        self.start_bat = self.root_dir / "start.bat"

    def get_current_version(self):
        """Reads start.bat to find LATEST_VERSION."""
        if not self.start_bat.exists():
            return "Unknown"
        
        try:
            with open(self.start_bat, "r", encoding="utf-8") as f:
                content = f.read()
                # Match set "LATEST_VERSION=v..."
                match = re.search(r'set "LATEST_VERSION=([^"]+)"', content)
                if match:
                    return match.group(1)
                # Fallback for non-quoted
                match = re.search(r'set LATEST_VERSION=([^\s]+)', content)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"Error reading start.bat: {e}")
        return "Unknown"

    def list_versions(self):
        """Lists all subdirectories in releases/ folder."""
        if not self.releases_dir.exists():
            return []
        
        versions = []
        for item in self.releases_dir.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                versions.append(item.name)
        
        # Sort versions semantically if possible, otherwise alphabetically
        try:
            versions.sort(key=lambda s: list(map(int, s.lstrip('v').split('.'))), reverse=True)
        except:
            versions.sort(reverse=True)
            
        return versions

    def switch_version(self, target_version):
        """Updates start.bat to point to target_version."""
        if not (self.releases_dir / target_version).exists():
            return False, f"Version {target_version} does not exist."

        if not self.start_bat.exists():
             return False, "start.bat not found."

        try:
            with open(self.start_bat, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            new_lines = []
            updated = False
            for line in lines:
                if "set \"LATEST_VERSION=" in line or "set LATEST_VERSION=" in line:
                    new_lines.append(f'set "LATEST_VERSION={target_version}"\n')
                    updated = True
                else:
                    new_lines.append(line)
            
            if not updated:
                return False, "Could not find LATEST_VERSION setting in start.bat"

            with open(self.start_bat, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            return True, f"Successfully switched to {target_version}. Please restart the application."
        except Exception as e:
            return False, f"Error updating start.bat: {e}"
