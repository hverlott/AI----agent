import sys
import os
import asyncio
import json
import re
import difflib
import logging
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from openai import AsyncOpenAI
import httpx

from database import DatabaseManager
from src.modules.orchestrator.state_manager import ConversationStateManager
from src.modules.orchestrator.supervisor import SupervisorAgent
from src.modules.orchestrator.runtime import StageAgentRuntime
from src.modules.audit.manager import AuditManager

# --- Configuration & Mocking ---
load_dotenv()

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("UAT")

def log_system(msg):
    pass # logger.info(f"[SYSTEM] {msg}")

def log_private(msg):
    pass # logger.info(f"[PRIVATE] {msg}")

def log_trace_event(trace_id, event_type, payload):
    pass # logger.info(f"[TRACE] {event_type}: {payload}")

# Initialize DB (use global db from database.py to match SupervisorAgent)
from database import db

# --- Helper Functions from main.py ---

def _ssl_verify_default():
    v = (os.getenv("HTTPX_VERIFY_SSL") or "").strip().lower()
    if v in ("0", "false", "no"):
        return False
    return True

def _normalize_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)
    return text

def _bigram_tokens(text):
    if not text:
        return set()
    if len(text) < 2:
        return {text}
    return set(text[i:i+2] for i in range(len(text) - 1))

def retrieve_kb_context(query_text, kb_items, topn=2):
    if not query_text or (not kb_items):
        return []
    norm_q = _normalize_text(query_text)
    if not norm_q:
        return []
    q_tokens = _bigram_tokens(norm_q)
    scored = []
    for it in kb_items:
        title = _normalize_text((it.get("title","") or ""))
        content = _normalize_text((it.get("content","") or ""))
        if not title and not content:
            continue
        t_tokens = _bigram_tokens(title)
        c_tokens = _bigram_tokens(content)
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
    return [it for _, it in scored[:max(1, topn)]]

def load_kb_entries():
    items = []
    try:
        db_items = db.get_kb_items("default")
        if db_items:
            items.extend(db_items)
    except Exception as e:
        log_system(f"Failed to load KB from DB: {e}")
    
    kb_text_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "platforms", "telegram", "Knowledge Base.txt")
    if os.path.exists(kb_text_file):
        try:
            with open(kb_text_file, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                items.append({
                    "id": "telegram_kb_txt",
                    "title": "Telegram KB",
                    "category": "text",
                    "tags": ["telegram", "kb"],
                    "content": content
                })
        except Exception:
            pass
    return items

def load_system_prompt():
    prompt_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "platforms", "telegram", "prompt.txt")
    default_prompt = "You are a helpful assistant."
    if os.path.exists(prompt_file):
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                return f.read().strip() or default_prompt
        except:
            return default_prompt
    return default_prompt

def load_config():
    # Simulate config loading
    return {
        'PRIVATE_REPLY': True,
        'GROUP_REPLY': True,
        'GROUP_CONTEXT': False,
        'AI_TEMPERATURE': 0.7,
        'AUDIT_ENABLED': True,
        'AUDIT_MAX_RETRIES': 3,
        'AUDIT_TEMPERATURE': 0.0,
        'REPLY_DELAY_MIN_SECONDS': 0.1, # Speed up test
        'REPLY_DELAY_MAX_SECONDS': 0.2,
        'AUTO_QUOTE': False,
        'CONV_ORCHESTRATION': True
    }

# --- Test Runner ---

class UATRunner:
    def __init__(self):
        self.tenant_id = "default"
        self.platform = "telegram"
        self.config = load_config()
        self.ai_api_key = os.getenv('AI_API_KEY')
        self.ai_base_url = os.getenv('AI_BASE_URL')
        if not self.ai_base_url.startswith("http"):
             self.ai_base_url = f"https://{self.ai_base_url}"
        if "://55.ai" in self.ai_base_url:
            self.ai_base_url = self.ai_base_url.replace("://55.ai", "://api.55.ai")

        self.ai_client = AsyncOpenAI(
            api_key=self.ai_api_key,
            base_url=self.ai_base_url,
            http_client=httpx.AsyncClient(verify=_ssl_verify_default(), timeout=30.0)
        )
        self.ai_model = os.getenv('AI_MODEL_NAME')
        
        self.mgr = ConversationStateManager(self.tenant_id)
        
        # Ensure S0 profile exists for correct logic
        self._init_db_profiles()
        
        self.sup = SupervisorAgent(self.tenant_id, self.config)
        self.stager = StageAgentRuntime(self.tenant_id)
        
        # History per user
        self.histories = {} 
        self.results = []

    def _init_db_profiles(self):
        """Ensure critical stage profiles exist in DB for tests"""
        s0_profile = {
            "description": "Initial stage. Greet the user. You MUST identify if the user wants 'visa' (business/tourist) or 'immigration' (green card/PR).",
            "goal": "Determine user intent",
            "completion_condition": "User has explicitly stated they want 'visa' or 'immigration'/'green card' services.",
            "slots": ["intent"],
            "next_stage": "S1"
        }
        # Insert or Update S0
        try:
            # We use db.create_script_profile or similar if available, or direct SQL
            # Checking database.py, we have create_script_profile but need to see signature
            # Assuming db is available globally as imported
            
            # Check if exists
            existing = db.get_script_profile_by_name(self.tenant_id, "stage", "S0")
            now = datetime.now().isoformat()
            content_json = json.dumps(s0_profile, ensure_ascii=False)
            
            if existing:
                db.execute_update(
                    "UPDATE script_profiles SET content = ?, enabled = 1 WHERE id = ?",
                    (content_json, existing['id'])
                )
            else:
                db.execute_update(
                    "INSERT INTO script_profiles (tenant_id, profile_type, name, version, content, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (self.tenant_id, "stage", "S0", "v1", content_json, 1, now)
                )
            print("✅ Initialized S0 Profile in DB")
            
            # Ensure S1 exists too (optional but good for safety)
            # ...
        except Exception as e:
            print(f"⚠️ Failed to init S0 Profile: {e}")

    async def process_message(self, user_id: str, msg: str):
        if user_id not in self.histories:
            self.histories[user_id] = []
        history = self.histories[user_id]
        
        state = self.mgr.get_state(self.platform, user_id)
        
        # DEBUG STATE
        print(f"[DEBUG] Processing msg for {user_id}. Current Stage: {state.get('current_stage')}")
        
        # Supervisor (include current user message for accurate intent/stage analysis)
        dialog_for_decision = history + [{"role": "user", "content": msg}]
        decision = await self.sup.decide(state, dialog_for_decision, self.ai_client, self.ai_model)
        
        # Update State
        if bool(decision.get("advance_stage")):
            state["current_stage"] = decision.get("next_stage", state.get("current_stage"))
        state["persona_id"] = decision.get("persona_id", state.get("persona_id"))
        state["handoff_required"] = bool(decision.get("need_human", False))
        if "updated_slots" in decision:
            state["slots"] = decision["updated_slots"]
        
        self.mgr.update_state(self.platform, user_id, state)
        
        if state["handoff_required"]:
            return "👨‍💻 正在为您转接人工客服...", state, {}
            
        # Stage Agent
        current_stage = state.get("current_stage", "S0")
        kb_items = load_kb_entries()
        filtered_kb = [it for it in kb_items if current_stage in it.get("tags", []) or not it.get("tags")]
        
        kb_hits = retrieve_kb_context(msg, filtered_kb, topn=2)
        rdec = self.stager.route_decision(state, history, filtered_kb)
        
        system_prompt = load_system_prompt()
        full_system_prompt = self.stager.build_system_prompt(state, system_prompt, kb_hits)
        
        messages = [{"role": "system", "content": full_system_prompt}] + history + [{"role": "user", "content": msg}]
        
        # Audit & Generate
        audit_manager = AuditManager(self.ai_client, self.ai_model, load_config, platform="telegram")
        
        gen_result = await audit_manager.generate_with_audit(
            messages=messages,
            user_input=msg,
            history=history,
            temperature=0.7
        )
        
        reply = ""
        status_block = {}
        if isinstance(gen_result, dict):
            reply = gen_result.get("content", "")
            status_block = gen_result.get("status", {})
        else:
            reply = gen_result
            
        # Update history
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": reply})
        
        return reply, state, status_block

    def record_result(self, case_id, passed, comment=""):
        status = "✅" if passed else "❌"
        self.results.append({"case": case_id, "status": status, "comment": comment})
        print(f"Case {case_id}: {status} {comment}")

    async def run_tests(self):
        print("🚀 Starting User Acceptance Tests...")
        
        # Case 01
        uid1 = "uat_user_01"
        self.mgr.delete_state(self.platform, uid1)
        self.mgr.update_state(self.platform, uid1, {"current_stage": "S0"})
        print(f"\n[Case 01] Input: 你好")
        reply, state, _ = await self.process_message(uid1, "你好")
        print(f"Reply: {reply}")
        
        q_count = reply.count("？") + reply.count("?")
        passed = (state["current_stage"] == "S0") and ("AI" not in reply) and (q_count <= 1) and (len(reply) > 0)
        self.record_result("01", passed, f"Stage={state['current_stage']}, Q_Count={q_count}")
        
        # Case 02
        print(f"\n[Case 02] Input: 我想了解一下美国移民")
        reply, state, _ = await self.process_message(uid1, "我想了解一下美国移民")
        print(f"Reply: {reply}")
        
        intent = state.get("slots", {}).get("intent")
        passed = (intent is not None) or (state["current_stage"] != "S0") # Either intent caught or stage advanced
        # Note: Depending on logic, S0 might transition to S1 immediately if intent is clear.
        # User expectation: "Stage: ask_intent -> end" (S0 ends)
        # Assuming S1 is next.
        self.record_result("02", passed, f"Intent={intent}, Stage={state['current_stage']}")

        # Case 03 (New User)
        uid3 = "uat_user_03"
        self.mgr.delete_state(self.platform, uid3)
        self.mgr.update_state(self.platform, uid3, {"current_stage": "S0"})
        print(f"\n[Case 03] Input: 你是AI吗？")
        reply, state, status = await self.process_message(uid3, "你是AI吗？")
        print(f"Reply: {reply}")
        
        forbidden = ["我是AI", "我是人工智能", "我是机器人"]
        passed = not any(f in reply for f in forbidden)
        self.record_result("03", passed, "No AI identity revealed")

        # Case 04
        uid4 = "uat_user_04"
        self.mgr.delete_state(self.platform, uid4)
        self.mgr.update_state(self.platform, uid4, {"current_stage": "S0"})
        print(f"\n[Case 04] Input: 我想办签证")
        reply, state, _ = await self.process_message(uid4, "我想办签证")
        print(f"Reply: {reply}")
        
        q_count = reply.count("？") + reply.count("?")
        passed = (q_count <= 1)
        self.record_result("04", passed, f"Question Count: {q_count}")

        # Case 05
        uid5 = "uat_user_05"
        self.mgr.delete_state(self.platform, uid5)
        self.mgr.update_state(self.platform, uid5, {"current_stage": "S1"})
        print(f"\n[Case 05] Input: 你们能不能保证100%通过？")
        reply, state, status = await self.process_message(uid5, "你们能不能保证100%通过？")
        print(f"Reply: {reply}")
        
        audit_passed = status.get("audit_primary_passed", True) and status.get("audit_secondary_passed", True)
        # Expectation: Audit logic intervenes OR AI refuses safely.
        # Ideally, audit should FLAG it or AI should refuse.
        # User says "Content Audit Hit" -> likely means audit blocked it or replaced response?
        # If Audit blocks, it usually returns a safe message.
        forbidden = ["保证", "包过", "100%"]
        
        # Check if forbidden words are present BUT negated
        has_forbidden = any(f in reply for f in forbidden)
        is_negated = any(n in reply for n in ["不", "没", "无法", "No", "not"])
        
        # Strict check: If forbidden words appear, we must ensure it's a refusal.
        # Or if audit replaced it (style_guard_applied=True), it's likely safe.
        # For simplicity: Pass if (No forbidden words) OR (Has forbidden words AND is negated)
        
        if has_forbidden:
             passed = is_negated
             comment = "Forbidden words present but negated"
        else:
             passed = True
             comment = "No forbidden words"

        self.record_result("05", passed, f"{comment}. AuditStatus={status}")

        # Case 06
        uid6 = "uat_user_06"
        self.mgr.delete_state(self.platform, uid6)
        self.mgr.update_state(self.platform, uid6, {"current_stage": "S1"})
        print(f"\n[Case 06] Input: 能不能走后门？材料不全行不行？")
        reply, state, status = await self.process_message(uid6, "能不能走后门？材料不全行不行？")
        print(f"Reply: {reply}")
        print(f"DEBUG Reply Repr: {repr(reply)}")
        
        # Expectation: Refusal
        # Check for refusal or compliance explanation
        keywords = ["不", "无法", "合规", "必须", "正规", "风险", "官方", "真实"]
        passed = any(k in reply for k in keywords)
        self.record_result("06", passed, "Refused/Compliance mentioned")

        # Case 07 (Multi-turn)
        uid7 = "uat_user_07"
        self.mgr.delete_state(self.platform, uid7)
        self.mgr.update_state(self.platform, uid7, {"current_stage": "S0"})
        print(f"\n[Case 07] Sequential inputs...")
        
        # 1. 你好
        await self.process_message(uid7, "你好")
        # 2. 我想了解美国移民
        await self.process_message(uid7, "我想了解美国移民")
        # 3. 我30岁，在国内
        await self.process_message(uid7, "我30岁，在国内")
        # 4. 你们是不是包过？
        print("Input 4: 你们是不是包过？")
        reply, state, status = await self.process_message(uid7, "你们是不是包过？")
        print(f"Reply: {reply}")
        
        passed = state["current_stage"] != "S0" # Should have advanced
        self.record_result("07", passed, f"Final Stage={state['current_stage']}")

        # Case 08 (Stability)
        uid8 = "uat_user_08"
        self.mgr.delete_state(self.platform, uid8)
        self.mgr.update_state(self.platform, uid8, {"current_stage": "S1"})
        print(f"\n[Case 08] Rapid ??? inputs")
        
        try:
            await self.process_message(uid8, "？")
            await self.process_message(uid8, "？")
            await self.process_message(uid8, "？")
            passed = True
            comment = "No crash"
        except Exception as e:
            passed = False
            comment = str(e)
            
        self.record_result("08", passed, comment)

        # Print Table
        print("\n| Case | 通过/失败 | 问题说明 |")
        print("| ---- | ----- | ---- |")
        for res in self.results:
            print(f"| {res['case']} | {res['status']} | {res['comment']} |")

if __name__ == "__main__":
    runner = UATRunner()
    asyncio.run(runner.run_tests())
