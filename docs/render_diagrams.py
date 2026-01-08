import os
import re
import httpx
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOC_PATH = BASE_DIR / "docs" / "System-Architecture.md"
IMG_DIR = BASE_DIR / "docs" / "images"

def slugify(title: str, fallback: str, index: int):
    s = title.strip().lower()
    s = re.sub(r"[^\w\s-]+", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s)
    s = s or fallback
    return f"{index:02d}-{s}.png"

def extract_mermaid_blocks(md_text: str):
    blocks = []
    lines = md_text.splitlines()
    current_title = ""
    i = 0
    index = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            current_title = line[3:].strip()
            i += 1
            continue
        if line.strip().startswith("```mermaid"):
            j = i + 1
            content = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                content.append(lines[j])
                j += 1
            index += 1
            filename = slugify(current_title, f"diagram-{index}", index)
            blocks.append((current_title, "\n".join(content), filename))
            i = j + 1
            continue
        i += 1
    return blocks

def render_to_png(mermaid_source: str) -> bytes:
    url = "https://kroki.io/mermaid/png"
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    with httpx.Client(timeout=30) as client:
        r = client.post(url, content=mermaid_source.encode("utf-8"), headers=headers)
        r.raise_for_status()
        return r.content

def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    if not DOC_PATH.exists():
        raise FileNotFoundError(f"{DOC_PATH} not found")
    text = DOC_PATH.read_text(encoding="utf-8")
    blocks = extract_mermaid_blocks(text)
    if not blocks:
        print("No mermaid blocks found")
        return
    for title, source, filename in blocks:
        try:
            png = render_to_png(source)
            out_path = IMG_DIR / filename
            out_path.write_bytes(png)
            print(f"Saved: {out_path}")
        except Exception as e:
            print(f"Failed: {title} -> {e}")

if __name__ == "__main__":
    main()
