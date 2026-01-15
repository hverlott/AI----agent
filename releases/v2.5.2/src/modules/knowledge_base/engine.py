import os
import difflib
import re
import json
import pickle
import numpy as np
from src.utils.text import normalize_text, bigram_tokens

class KBEngine:
    def __init__(self, client=None, embedding_model="text-embedding-3-small"):
        self.client = client  # OpenAI Compatible Client for Embeddings
        self.embedding_model = embedding_model

    def _get_embedding(self, text):
        if not self.client:
            return None
        try:
            text = text.replace("\n", " ")
            # Use configured model
            # Note: client.embeddings.create might need adjustment if using non-OpenAI client, 
            # but assuming standard OpenAI SDK interface here.
            # If model identifier is "provider:model", we might need to strip provider if client is already configured for it.
            # But usually client is generic. Let's assume model name is passed correctly.
            model_name = self.embedding_model
            if ":" in model_name:
                model_name = model_name.split(":", 1)[1]
                
            return self.client.embeddings.create(input=[text], model=model_name).data[0].embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def _cosine_similarity(self, v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    def load_vectors(self, tenant_id):
        path = f"data/tenants/{tenant_id}/chroma/vectors.pkl"
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except:
                pass
        return {}

    def retrieve_kb_context(self, query_text, kb_items, topn=3, tenant_id=None):
        if not query_text or (not kb_items):
            return []
        
        # 0. 尝试匹配 QA 库 (精确匹配)
        qa_pairs = []
        for it in kb_items:
            if it.get("category") in ["qa", "qa_txt"] or self._kb_is_qa_like(it):
                 # 简单解析
                 content = it.get("content", "")
                 if "Question:" in content and "Answer:" in content:
                     q = content.split("Question:", 1)[1].split("Answer:", 1)[0].strip()
                     a = content.split("Answer:", 1)[1].strip()
                     qa_pairs.append((q, a))
        
        if qa_pairs:
             direct_answer = self.match_qa_reply(query_text, qa_pairs)
             if direct_answer:
                 # 构造一个虚拟的 KB item 返回，让上层认为是完全匹配
                 return [{"title": "QA Match", "content": direct_answer, "score": 1.0, "source_file": "QA"}]

        # 1. Vector Search (if available) - 混合检索策略
        vector_candidates = []
        if tenant_id and self.client:
            vectors = self.load_vectors(tenant_id)
            if vectors:
                q_vec = self._get_embedding(query_text)
                if q_vec:
                    scored_vec = []
                    for it in kb_items:
                        vid = str(it.get("id"))
                        if vid in vectors:
                            score = self._cosine_similarity(q_vec, vectors[vid])
                            scored_vec.append((score, it))
                    
                    if scored_vec:
                        scored_vec.sort(key=lambda x: x[0], reverse=True)
                        # Threshold for vector similarity (e.g., 0.4)
                        vector_candidates = [it for s, it in scored_vec[:topn*2] if s > 0.4] # 取多一点备选

        # 2. Keyword Search (Difflib) - 关键词检索
        norm_q = normalize_text(query_text)
        keyword_candidates = []
        if norm_q:
            q_tokens = bigram_tokens(norm_q)
            scored = []
            for it in kb_items:
                title = normalize_text((it.get("title","") or ""))
                content = normalize_text((it.get("content","") or ""))
                if not title and not content:
                    continue
                t_tokens = bigram_tokens(title)
                c_tokens = bigram_tokens(content)
                title_overlap = len(q_tokens & t_tokens) / max(1, len(q_tokens))
                content_overlap = len(q_tokens & c_tokens) / max(1, len(q_tokens))
                bonus = 0.0
                if norm_q in title or title in norm_q:
                    bonus += 0.6
                if norm_q in content or content in norm_q:
                    bonus += 0.3
                base = 2.0 * title_overlap + 1.0 * content_overlap + bonus
                if base == 0.0:
                    text_all = title + content
                    base = difflib.SequenceMatcher(None, norm_q, text_all).ratio() * 0.5
                scored.append((base, it))
            scored.sort(key=lambda x: x[0], reverse=True)
            keyword_candidates = [it for _, it in scored[:topn*2]]

        # 3. Hybrid Merge (RRF - Reciprocal Rank Fusion 简化版)
        # 这里简单地取并集，去重，然后按某种加权重新排序，或者直接交替合并
        # 简单策略：优先向量结果，如果向量结果少于 topn，用关键词结果补充
        
        final_results = []
        seen_ids = set()
        
        # 先加向量的高分结果
        for it in vector_candidates:
            if it['id'] not in seen_ids:
                final_results.append(it)
                seen_ids.add(it['id'])
        
        # 再加关键词结果补充
        for it in keyword_candidates:
            if it['id'] not in seen_ids:
                final_results.append(it)
                seen_ids.add(it['id'])
                
        return final_results[:topn]

    def load_qa_pairs(self, file_path):
        qa_pairs = []
        if not file_path or (not os.path.exists(file_path)):
            return qa_pairs
        try:
            raw_lines = self._read_lines_with_fallback(file_path)
            pending_qs = []
            collecting = False
            answer_lines = []
            for line in raw_lines:
                stripped = line.strip()
                if not stripped:
                    if collecting and pending_qs:
                        answer_lines.append("")
                    continue
                if stripped.startswith('#'):
                    continue
                if '||' in stripped:
                    q, a = stripped.split('||', 1)
                    q = q.strip()
                    a = a.strip()
                    if q and a:
                        variants = self._split_variants(q)
                        for v in variants:
                            qa_pairs.append((v, a))
                    continue
                if stripped.lower().startswith('q:'):
                    if pending_qs and answer_lines:
                        answer = "\n".join(answer_lines).strip()
                        for v in pending_qs:
                            qa_pairs.append((v, answer))
                    pending_qs = self._split_variants(stripped[2:].strip())
                    collecting = False
                    answer_lines = []
                    continue
                if stripped.lower().startswith('a:') and pending_qs:
                    collecting = True
                    answer_lines.append(stripped[2:].strip())
                    continue
                if collecting and pending_qs:
                    answer_lines.append(stripped)
            if pending_qs and answer_lines:
                answer = "\n".join(answer_lines).strip()
                for v in pending_qs:
                    qa_pairs.append((v, answer))
        except Exception:
            return []
        return qa_pairs

    def match_qa_reply(self, message_text, qa_pairs):
        if not message_text:
            return None
        msg = message_text.strip()
        if not msg:
            return None
        norm_msg = normalize_text(msg)
        if not norm_msg:
            return None
        msg_tokens = bigram_tokens(norm_msg)
        for q, a in qa_pairs:
            if not q:
                continue
            norm_q = normalize_text(q)
            if not norm_q:
                continue
            if norm_q in norm_msg or norm_msg in norm_q:
                return a
            q_tokens = bigram_tokens(norm_q)
            if q_tokens:
                overlap = len(msg_tokens & q_tokens) / max(1, len(q_tokens))
                if overlap >= 0.45:
                    return a
            ratio = difflib.SequenceMatcher(None, norm_q, norm_msg).ratio()
            if ratio >= 0.5:
                return a
        return None

    def _read_lines_with_fallback(self, file_path):
        encodings = ["utf-8", "gbk", "cp936"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read().splitlines()
            except UnicodeDecodeError:
                continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().splitlines()

    def _split_variants(self, text):
        parts = re.split(r"[\\/|｜]+", text)
        return [p.strip() for p in parts if p.strip()]

    def detect_qa_only(self, query_text, kb_hits):
        reason = {}
        if not self._is_clear_question(query_text or ""):
            return False, {}
        if kb_hits:
            if any(self._kb_is_qa_like(it) for it in kb_hits):
                reason["kb_doc_type"] = True
        if self._is_single_point_question(query_text or ""):
            reason["single_clear_question"] = True
        if not reason:
            return False, {}
        return True, reason

    def _is_single_point_question(self, text):
        if not text:
            return False
        t = text.strip()
        if len(t) <= 2:
            return False
        if re.search(r"(是什么|怎么算|如何|是否|费用|价格|收费|流程|规则|计算|怎么算|怎么计算)", t):
            if not re.search(r"(、|以及|和|并且)", t):
                return True
        return False

    def _is_clear_question(self, text):
        if not text:
            return False
        t = text.strip()
        if len(t) < 6:
            return False
        if re.search(r"[?？]", t):
            return True
        if re.search(r"(怎么|如何|是否|多少|为什么|为什麼|規則|规则|計算|计算|流程|价格|費用|费用|收费)", t):
            return True
        return False

    def _kb_is_qa_like(self, item):
        cat = (item.get("category","") or "").lower()
        title = (item.get("title","") or "").lower()
        tags = item.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = [tags]
        tlist = [str(x).lower() for x in tags] if isinstance(tags, list) else []
        qa_keys = ["客服话术","q&a","qa","faq","问答","话术"]
        for k in qa_keys:
            if k in cat or k in title or any(k in str(tx) for tx in tlist):
                return True
        return False
