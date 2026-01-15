from typing import Dict, List, Any
from datetime import datetime
import os
import json
from src.core.database import db
from src.modules.orchestrator.state_manager import ConversationStateManager

class StageAgentRuntime:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    def _load_binding_json(self) -> Dict[str, Any]:
        prof = db.get_script_profile_by_name(self.tenant_id, "binding", "binding_default", "v1")
        content = prof.get("content") or "{}"
        try:
            return json.loads(content)
        except Exception:
            return {}
    def get_stage_profile(self, stage_name: str) -> Dict[str, Any]:
        prof = db.get_script_profile_by_name(self.tenant_id, "stage", stage_name)
        if not prof:
            return {}
        try:
            return json.loads(prof.get("content") or "{}")
        except:
            return {}

    def get_persona_profile(self, persona_name: str) -> Dict[str, Any]:
        prof = db.get_script_profile_by_name(self.tenant_id, "persona", persona_name)
        if not prof:
            return {}
        try:
            return json.loads(prof.get("content") or "{}")
        except:
            return {}

    def build_system_prompt(self, state: Dict[str, Any], base_system_prompt: str, kb_items: List[Dict[str, Any]], bound_ai_id: str = None) -> str:
        stage_name = state.get("current_stage") or "S0"
        persona_name = state.get("persona_id") or "calm_professional"
        
        stage_prof = self.get_stage_profile(stage_name)
        persona_prof = self.get_persona_profile(persona_name)
        
        parts = [base_system_prompt]
        
        if persona_prof:
            p_desc = persona_prof.get("description") or ""
            p_style = persona_prof.get("style") or ""
            if p_desc or p_style:
                parts.append(f"\n【当前人设 ({persona_name})】\n{p_desc}\n回复风格: {p_style}")
        
        if stage_prof:
            s_desc = stage_prof.get("description") or ""
            s_goal = stage_prof.get("goal") or ""
            s_const = stage_prof.get("constraints") or ""
            parts.append(f"\n【当前阶段 ({stage_name})】\n阶段描述: {s_desc}\n当前目标: {s_goal}")
            if s_const:
                parts.append(f"约束条件: {s_const}")

        tools = []
        try:
            skills = db.get_enabled_skills(self.tenant_id, bound_ai_id)
            if skills:
                for sk in skills:
                    raw_cfg = sk.get("config_json") or ""
                    try:
                        cfg = json.loads(raw_cfg) if isinstance(raw_cfg, str) and raw_cfg else {}
                    except Exception:
                        cfg = {}
                    
                    apply_mode = cfg.get("apply_mode", "both")
                    if apply_mode not in ("script_only", "both"):
                        continue

                    # 1. Text Injection (Legacy)
                    desc = sk.get("description") or ""
                    tpl = (cfg.get("template") or "").strip()
                    if tpl:
                         parts.append(f"\n【技能: {sk.get('name')}】\n{desc}\n{tpl}")

                    # 2. Tool Definition (OpenAI Format)
                    tool_def = cfg.get("tool_definition")
                    if tool_def:
                        tools.append({
                            "type": "function",
                            "function": tool_def
                        })

        except Exception:
            pass
        
        return "\n".join(parts), tools

    def resolve_binding(self, state: Dict, ctx: Dict) -> Dict:
        bind = self._load_binding_json()
        routes = bind.get("routes") or []
        risk_order = {"low": 0, "medium": 1, "high": 2, "unknown": 1}
        candidates = []
        for r in routes:
            stg = r.get("stage") or "*"
            per = r.get("persona") or "*"
            if stg not in ["*", state.get("current_stage")]:
                continue
            if per not in ["*", state.get("persona_id")]:
                continue
            kb_req = bool(r.get("kb_required", False))
            if kb_req and int(ctx.get("kb_hits", 0)) <= 0:
                continue
            min_len = int(r.get("min_msg_len", 0))
            if int(ctx.get("msg_len", 0)) < min_len:
                continue
            imin = r.get("intent_min")
            if imin is not None and float(ctx.get("intent_score", 0.0)) < float(imin):
                continue
            imax = r.get("intent_max")
            if imax is not None and float(ctx.get("intent_score", 0.0)) > float(imax):
                continue
            rmax = r.get("risk_max")
            if rmax:
                cur_r = ctx.get("risk_level", "unknown")
                if risk_order.get(cur_r, 1) > risk_order.get(str(rmax).lower(), 1):
                    continue
            candidates.append(r)
        
        if candidates:
            # Enhanced scoring: weight + bonuses
            # Bonus: specific stage/persona match gets +5 each (vs "*")
            # Bonus: kb_required=True and hit gets +2
            # Bonus: risk/intent constraint presence gets +1
            def calc_score(rule):
                base = float(rule.get("weight", 0.0))
                bonus = 0.0
                if rule.get("stage") != "*": bonus += 5.0
                if rule.get("persona") != "*": bonus += 5.0
                if rule.get("kb_required"): bonus += 2.0
                if rule.get("intent_min") or rule.get("intent_max"): bonus += 1.0
                if rule.get("risk_max"): bonus += 1.0
                return base + bonus

            candidates.sort(key=calc_score, reverse=True)
            r = candidates[0]
            # Inject calculated score and ID into matched rule for visibility
            r["_final_score"] = calc_score(r)
            # Find original index in routes to use as ID if no explicit ID
            try:
                # This might be slow if routes is huge, but it's usually small.
                # Or we could have preserved the index during iteration.
                # Re-finding it for simplicity.
                r["_rule_id"] = routes.index(r)
            except:
                r["_rule_id"] = -1
            
            return {
                "model": r.get("model"),
                "temperature": float(r.get("temperature", 0.7)),
                "matched_rule": r
            }
        return {
            "model": (bind.get("default") or {}).get("model"),
            "temperature": float((bind.get("default") or {}).get("temperature", 0.7)),
            "matched_rule": {}
        }
    def route_decision(self, state: Dict, recent_dialog: List[Dict], kb_items: List[Dict]) -> Dict:
        last = ""
        if recent_dialog:
            last = recent_dialog[-1].get("content") or ""
        ctx = {
            "kb_hits": len(kb_items or []),
            "msg_len": len(last or ""),
            "intent_score": float(state.get("intent_score", 0.0) or 0.0),
            "risk_level": state.get("risk_level") or "unknown",
            "current_stage": state.get("current_stage"),
            "persona_id": state.get("persona_id"),
            "user_msg": last
        }
        sel = self.resolve_binding(state, ctx)
        provider = self.resolve_ai_provider(state)
        model = sel.get("model") or provider.get("model")
        base_url = provider.get("base_url")
        
        decision_result = {
            "model": model,
            "base_url": base_url,
            "temperature": sel.get("temperature", 0.7),
            "context": ctx,
            "matched_rule": sel.get("matched_rule") or {}
        }
        
        # Log to DB for playback/audit
        try:
            from database import db
            # Need user_id from state? Assuming state might have it or use 'system'
            user_id = state.get("user_id") or "unknown"
            # We store the FULL decision context in decision_json
            db.log_routing_decision(self.tenant_id, user_id, "telegram", decision_result)
        except Exception:
            pass
            
        return decision_result
    def resolve_ai_provider(self, state: Dict) -> Dict:
        path = os.path.join("data", "tenants", self.tenant_id, "ai_providers.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            providers = data.get("providers") or []
            if not providers:
                raise ValueError("no providers")
            providers.sort(key=lambda p: int(p.get("weight", 0)), reverse=True)
            p = providers[0]
            return {
                "base_url": p.get("base_url"),
                "model": p.get("model"),
                "timeout": int(p.get("timeout", 15))
            }
        except Exception:
            return {
                "base_url": os.getenv("AI_BASE_URL") or "https://api.openai.com/v1",
                "model": os.getenv("AI_MODEL_NAME") or "gpt-4o-mini",
                "timeout": 15
            }
    async def generate(self, state: Dict, recent_dialog: List[Dict], kb_items: List[Dict], ai_client=None, model_name: str = None, system_prompt: str = None, temperature: float = 0.7) -> Dict:
        persona = state.get("persona_id") or "calm_professional"
        stage = state.get("current_stage") or "S0"
        last = ""
        if recent_dialog:
            last = recent_dialog[-1].get("content") or ""
        kb_hint = ""
        if kb_items:
            for it in kb_items[:1]:
                kb_hint = (it.get("title") or "")[:80]
                break
        if ai_client and model_name and system_prompt:
            msgs = []
            meta = f"Stage={stage} Persona={persona}"
            sys_with_meta = system_prompt + "\n\n" + meta
            msgs.append({"role": "system", "content": sys_with_meta})
            if recent_dialog:
                msgs.extend(recent_dialog)
            msgs.append({"role": "user", "content": last})
            try:
                resp = await ai_client.chat.completions.create(
                    model=model_name,
                    messages=msgs,
                    temperature=temperature,
                    max_tokens=500
                )
                content = resp.choices[0].message.content
                
                # Capture Usage
                usage = resp.usage
                tokens = 0
                usage_info = {}
                if usage:
                    tokens = usage.total_tokens
                    usage_info = {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": tokens,
                        "model": model_name
                    }
                
                return {
                    "reply_draft": content,
                    "generated_at": datetime.now().isoformat(),
                    "usage": usage_info
                }
            except Exception as e:
                # Log error
                try:
                    db.log_audit(self.tenant_id, "System", "generation_error", {"error": str(e)})
                except:
                    pass
                
                return {
                    "reply_draft": "System is currently experiencing high load. Please try again later.",
                    "generated_at": datetime.now().isoformat(),
                    "usage": {},
                    "error": str(e)
                }
        
        # Fallback for no AI client (Debug Mode)
        text = f"[{stage}|{persona}] {last}".strip()
        if kb_hint:
            text = f"{text} ({kb_hint})"
        return {
            "reply_draft": text,
            "generated_at": datetime.now().isoformat()
        }
