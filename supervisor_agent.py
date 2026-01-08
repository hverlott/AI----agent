import json
from typing import Dict, List
from database import db

class SupervisorAgent:
    def __init__(self, tenant_id: str, policy: Dict = None):
        self.tenant_id = tenant_id
        self.policy = policy or {}

    async def decide(self, state: Dict, recent_dialog: List[Dict], ai_client=None, model_name: str = None) -> Dict:
        cur = state.get("current_stage") or "S0"
        next_stage = cur
        advance = False
        intent = float(state.get("intent_score") or 0.0)
        risk = state.get("risk_level") or "unknown"
        persona = state.get("persona_id") or "calm_professional"
        need_human = False
        flags = []
        
        # 1. Check Handoff (Basic Keyword Match)
        text = ""
        if recent_dialog:
            for m in recent_dialog[-3:]:
                if m.get("role") == "user":
                    c = m.get("content") or ""
                    text += c + "\n"
        # Intent inference
        inferred_intent = None
        low = text.lower()
        if any(k in low for k in ["移民", "永居", "绿卡", "immigration"]):
            inferred_intent = "immigration"
        elif any(k in low for k in ["签证", "visa"]):
            inferred_intent = "visa"
        
        if any(k in text.lower() for k in ["help", "客服", "人工"]):
            need_human = True
            flags.append("handoff_requested")

        # 2. Load Current Stage Profile
        stage_prof_raw = db.get_script_profile_by_name(self.tenant_id, "stage", cur)
        stage_prof = {}
        if stage_prof_raw:
            try:
                stage_prof = json.loads(stage_prof_raw.get("content") or "{}")
            except:
                pass
        
        # 3. Check Completion / Advancement / Slots
        completion_condition = stage_prof.get("completion_condition")
        target_next_stage = stage_prof.get("next_stage")
        required_slots = stage_prof.get("slots") or []
        
        updated_slots = state.get("slots") or {}
        if inferred_intent and not updated_slots.get("intent"):
            updated_slots["intent"] = inferred_intent
        
        total_usage = {"total_tokens": 0, "cost": 0.0}
        
        if ai_client and model_name:
            # Use LLM to check condition and extract slots
            result = await self._analyze_stage_progress(
                ai_client, model_name, 
                cur, stage_prof, updated_slots, recent_dialog
            )
            
            if "_usage" in result:
                total_usage = result["_usage"]

            # Update Slots
            if result.get("extracted_slots"):
                updated_slots.update(result["extracted_slots"])
            
            # Check Completion
            if result.get("completion_met"):
                advance = True
                if target_next_stage:
                    next_stage = target_next_stage
                else:
                    if cur == "S0": next_stage = "S1"
                    elif cur == "S1": next_stage = "S2"
                    elif cur == "S2": next_stage = "S3"
        else:
            # Fallback to Intent-based Logic
            if intent >= 0.6 and cur == "S1":
                next_stage = "S2"
                advance = True
            elif intent >= 0.8 and cur in ["S2", "S3"]:
                next_stage = "S4"
                advance = True
            # elif cur == "S0":
            #     next_stage = "S1"
            #     advance = True

        agent_profile_id = f"{next_stage}_{persona}_v1"
        return {
            "current_stage": cur,
            "advance_stage": advance,
            "next_stage": next_stage,
            "persona_id": persona,
            "agent_profile_id": agent_profile_id,
            "next_action": "continue_or_advance",
            "need_human": need_human,
            "risk_flags": flags,
            "updated_slots": updated_slots,
            "usage": total_usage
        }

    async def _analyze_stage_progress(self, ai_client, model_name, stage_name, stage_prof, current_slots, history):
        condition = stage_prof.get("completion_condition") or "None"
        req_slots = stage_prof.get("slots") or []
        
        sys_prompt = f"""
You are a Conversation Supervisor.
Current Stage: {stage_name}
Completion Condition: "{condition}"
Required Slots to Collect: {req_slots}
Current Collected Slots: {json.dumps(current_slots, ensure_ascii=False)}

Task:
1. Extract any NEW values for Required Slots from the User's latest message.
2. Decide if the Completion Condition is met. (If slots are missing, usually it is NOT met).

Return JSON ONLY:
{{
    "extracted_slots": {{ "key": "value" }},
    "completion_met": true/false
}}
"""
        msgs = [{"role": "system", "content": sys_prompt}]
        msgs.extend(history[-4:])
        
        try:
            resp = await ai_client.chat.completions.create(
                model=model_name,
                messages=msgs,
                temperature=0.0,
                max_tokens=100,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content.strip()
            res = json.loads(content)
            
            # Capture usage
            if resp.usage:
                res["_usage"] = {
                    "prompt_tokens": resp.usage.prompt_tokens,
                    "completion_tokens": resp.usage.completion_tokens,
                    "total_tokens": resp.usage.total_tokens,
                    "model": model_name
                }
            return res
        except Exception as e:
            # Log the error for visibility
            try:
                db.log_audit(self.tenant_id, "System", "supervisor_error", {
                    "error": str(e),
                    "stage": stage_name,
                    "model": model_name
                })
            except:
                pass
            return {"extracted_slots": {}, "completion_met": False}

    async def _check_completion(self, ai_client, model_name, condition, history):
        # Deprecated in favor of _analyze_stage_progress
        pass
