import os
import re
import glob

def get_button_labels(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match st.button("Label") or st.button(label="Label")
    # Simple regex, might miss variables but good enough for static strings
    patterns = [
        r'st\.button\(\s*"([^"]+)"',
        r"st\.button\(\s*'([^']+)'",
        r'st\.button\(\s*label="([^"]+)"',
        r"st\.button\(\s*label='([^']+)'"
    ]
    labels = set()
    for p in patterns:
        matches = re.findall(p, content)
        labels.update(matches)
    return labels

def get_doc_content(doc_dir):
    content = ""
    for file in glob.glob(os.path.join(doc_dir, "*.md")):
        with open(file, 'r', encoding='utf-8') as f:
            content += f.read() + "\n"
    return content

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    admin_file = os.path.join(base_dir, "admin_multi.py")
    doc_dir = os.path.join(base_dir, "docs", "help_center", "v1.0", "zh_CN")
    
    print(f"Scanning Admin File: {admin_file}")
    buttons = get_button_labels(admin_file)
    print(f"Found {len(buttons)} buttons.")
    
    print(f"Scanning Docs Dir: {doc_dir}")
    doc_text = get_doc_content(doc_dir)
    
    found = 0
    missing = []
    
    for btn in buttons:
        # Check if button label exists in docs (simple string match)
        if btn in doc_text:
            found += 1
        else:
            missing.append(btn)
            
    print("-" * 30)
    print(f"Documentation Coverage: {found}/{len(buttons)} ({found/len(buttons)*100:.1f}%)")
    print("-" * 30)
    
    if missing:
        print("Missing Buttons in Docs:")
        for m in missing[:10]: # Show top 10
            print(f" - {m}")
        if len(missing) > 10:
            print(f"... and {len(missing)-10} more.")
            
if __name__ == "__main__":
    main()
