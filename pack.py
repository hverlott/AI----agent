import os
import shutil
import datetime
from pathlib import Path

def pack_project():
    # Setup paths
    root_dir = Path('.').resolve()
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    pkg_name = f"AI-Talk-Package-{date_str}"
    temp_dir = root_dir / pkg_name
    zip_name = f"{pkg_name}.zip"

    print(f"📦 Packaging project to {zip_name}...")

    # Clean previous
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    if (root_dir / zip_name).exists():
        os.remove(root_dir / zip_name)

    os.makedirs(temp_dir)

    # Define ignore patterns
    # We use a custom ignore for copytree
    def custom_ignore(path, names):
        ignored = set()
        for name in names:
            if name == '__pycache__' or name == '.git' or name.startswith('.venv'):
                ignored.add(name)
            elif name.endswith('.session') or name.endswith('.session-journal'):
                ignored.add(name)
            elif name.endswith('.log') or name == 'trace.jsonl':
                ignored.add(name)
            elif name == 'core.db':
                ignored.add(name)
            elif name == '.env':
                ignored.add(name)
            elif name == 'backups':
                ignored.add(name)
            elif name == 'node_modules':
                ignored.add(name)
            elif name == '.wwebjs_auth':
                ignored.add(name)
            elif name.endswith('.zip'):
                ignored.add(name)
        return ignored

    # 1. Root files
    print("  - Copying root files...")
    for file in root_dir.glob('*'):
        if file.is_file():
            # Filter extensions
            if file.suffix.lower() in ['.py', '.txt', '.bat', '.sh', '.md', '.spec'] or file.name == '.env.example':
                # Exclude specific files
                if file.name in ['reproduce_kb_issue.py'] or file.name.startswith('_tmp_') or file.name.startswith('test_'):
                    continue
                shutil.copy2(file, temp_dir)

    # 3. Directories
    dirs_to_copy = ['platforms', 'docs', 'data', 'tools', 'tests', '.streamlit']
    for d in dirs_to_copy:
        src = root_dir / d
        if src.exists():
            dst = temp_dir / d
            # We use copytree but we need to filter exclusions recursively
            # shutil.copytree support ignore callback
            try:
                shutil.copytree(src, dst, ignore=custom_ignore, symlinks=True)
                print(f"  - Copied {d}")
            except Exception as e:
                print(f"  - Failed to copy {d}: {e}")
        else:
            print(f"  - Skipped {d} (not found)")

    # 4. Sanitize / Reset Configuration Files
    print("🧹 Sanitizing configuration files...")
    
    # Define default contents
    tg_config_default = """# ========================================
# Telegram AI Bot - 功能配置
# ========================================

# 个人消息回复开关
PRIVATE_REPLY=on

# 群消息回复开关
GROUP_REPLY=on

# AI 会话编排引擎 (SOP/Persona/KB)
CONV_ORCHESTRATION=off

# 知识库直答（不走剧本）
KB_ONLY_REPLY=on

# 强制刷新知识库 (on/off)
KB_REFRESH=off

# 对话呈现模式 (ai_visible / human_simulated)
CONVERSATION_MODE=ai_visible

# 人工触发关键词（逗号分隔）
HANDOFF_KEYWORDS=人工,转客服

# 人工兜底话术
HANDOFF_MESSAGE=正在为您转接人工客服，请稍候...

# KB_ONLY兜底话术
KB_FALLBACK_MESSAGE=抱歉，暂时没有找到相关答案。

# AI 温度 (0.0-1.0)
AI_TEMPERATURE=0.7

# 自动引用
AUTO_QUOTE=off
QUOTE_INTERVAL_SECONDS=30.0
QUOTE_MAX_LEN=200

# 内容审核配置
AUDIT_ENABLED=on
AUDIT_MODE=local
AUDIT_SERVERS=http://127.0.0.1:8000
AUDIT_MAX_RETRIES=3
AUDIT_TEMPERATURE=0.0
AUDIT_GUIDE_STRENGTH=0.5
"""

    wa_config_default = """# ========================================
# WhatsApp AI Bot - 功能开关配置
# ========================================
# 个人消息回复开关
PRIVATE_REPLY=on
# 群消息回复开关
GROUP_REPLY=on
"""

    files_to_clean = {
        "platforms/telegram/config.txt": tg_config_default,
        "platforms/telegram/qa.txt": "# 在此处添加问答对\n# 格式：\n# Q: 问题\n# A: 答案\n",
        "platforms/telegram/Knowledge Base.txt": "# 在此处添加知识库内容 (Markdown 格式)\n",
        "platforms/telegram/prompt.txt": "你是一个智能客服机器人，请礼貌、专业地回答用户的问题。",
        "platforms/telegram/keywords.txt": "help\nsupport\n人工",
        "platforms/telegram/extra_kb.txt": None, # Delete
        "platforms/telegram/logs": None, # Delete content, keep dir? No, shutil.copytree ignore handles logs but let's be safe
        "platforms/whatsapp/config.txt": wa_config_default,
        "data/core.db": None,
        ".env": None
    }

    for rel_path, content in files_to_clean.items():
        file_path = temp_dir / rel_path
        
        # Handle deletion
        if content is None:
            if file_path.exists():
                try:
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    print(f"    - Removed {rel_path}")
                except Exception as e:
                    print(f"    - Failed to remove {rel_path}: {e}")
            continue

        # Handle overwrite
        if file_path.parent.exists():
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"    - Reset {rel_path}")
            except Exception as e:
                print(f"    - Failed to reset {rel_path}: {e}")

    # 5. Zip
    print(f"🗜️ Zipping...")
    # make_archive will create {pkg_name}.zip from {root_dir}/{pkg_name}
    shutil.make_archive(pkg_name, 'zip', root_dir, pkg_name)
    
    # Cleanup temp dir
    shutil.rmtree(temp_dir)
    
    final_zip = root_dir / zip_name
    if final_zip.exists():
        size_kb = final_zip.stat().st_size / 1024
        print(f"✅ Done! Package: {final_zip.name} ({size_kb:.1f} KB)")
        print(f"📍 Location: {final_zip}")
    else:
        print("❌ Error: Zip file not created.")

if __name__ == '__main__':
    pack_project()
