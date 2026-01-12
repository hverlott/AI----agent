import re
import difflib

def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)
    return text

def bigram_tokens(text):
    if not text:
        return set()
    if len(text) < 2:
        return {text}
    return set(text[i:i+2] for i in range(len(text) - 1))

def split_sentences(s):
    if not s:
        return []
    parts = re.split(r"[。！？!?\n]+", s)
    return [p.strip() for p in parts if p.strip()]

def calculate_similarity(a, b):
    if not a or not b:
        return 0.0
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0
    ta = bigram_tokens(na)
    tb = bigram_tokens(nb)
    if ta and tb:
        return len(ta & tb) / max(1, len(ta))
    return difflib.SequenceMatcher(None, na, nb).ratio()
