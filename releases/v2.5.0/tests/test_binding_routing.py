import unittest
import json
import sys
import os
# Ensure project root on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db
from src.modules.orchestrator.runtime import StageAgentRuntime

class BindingRoutingTests(unittest.TestCase):
    def test_route_decision_with_binding(self):
        tenant = "default"
        binding = {
            "routes": [
                {"stage": "S0", "persona": "calm_professional", "model": "deepseek-v3.1", "temperature": 0.5, "intent_min": 0.6, "risk_max": "high"}
            ],
            "default": {"model": "deepseek-v3.1", "temperature": 0.7}
        }
        db.upsert_script_profile(tenant, "binding", "binding_default", "v1", json.dumps(binding), True)
        stager = StageAgentRuntime(tenant)
        state = {"current_stage": "S0", "persona_id": "calm_professional", "intent_score": 0.7, "risk_level": "medium"}
        dec = stager.route_decision(state, [{"role":"user","content":"hi"}], [])
        self.assertEqual(dec.get("model"), "deepseek-v3.1")
        self.assertAlmostEqual(dec.get("temperature"), 0.5, places=2)
    def test_route_decision_fallback_on_intent(self):
        tenant = "default"
        binding = {
            "routes": [
                {"stage": "S0", "persona": "calm_professional", "model": "m-special", "temperature": 0.5, "intent_min": 0.9}
            ],
            "default": {"model": "deepseek-v3.1", "temperature": 0.7}
        }
        db.upsert_script_profile(tenant, "binding", "binding_default", "v1", json.dumps(binding), True)
        stager = StageAgentRuntime(tenant)
        state = {"current_stage": "S0", "persona_id": "calm_professional", "intent_score": 0.6}
        dec = stager.route_decision(state, [{"role":"user","content":"hello"}], [])
        self.assertEqual(dec.get("model"), "deepseek-v3.1")
    def test_weighted_rule_selection(self):
        tenant = "default"
        binding = {
            "routes": [
                {"stage": "S0", "persona": "calm_professional", "model": "m-low", "temperature": 0.5, "weight": 10},
                {"stage": "S0", "persona": "calm_professional", "model": "m-high", "temperature": 0.6, "weight": 20}
            ],
            "default": {"model": "deepseek-v3.1", "temperature": 0.7}
        }
        db.upsert_script_profile(tenant, "binding", "binding_default", "v1", json.dumps(binding), True)
        stager = StageAgentRuntime(tenant)
        state = {"current_stage": "S0", "persona_id": "calm_professional"}
        dec = stager.route_decision(state, [{"role":"user","content":"hello"}], [])
        self.assertEqual(dec.get("model"), "m-high")
        # Ensure final score is higher than weight due to stage/persona bonuses
        matched = dec.get("matched_rule")
        self.assertGreater(matched.get("_final_score", 0), 20)

    def test_score_calculation(self):
        # Test if specificity bonuses work
        tenant = "default"
        # Rule 1: specific S0, persona *, weight 10
        # Rule 2: specific S0, specific P1, weight 5 -> Should win due to bonus?
        # S0(+5) + * (+0) + 10 = 15
        # S0(+5) + P1(+5) + 5 = 15
        # Tie? Let's make Rule 2 weight 6 -> 16.
        binding = {
            "routes": [
                {"stage": "S0", "persona": "*", "model": "m-gen", "weight": 10},
                {"stage": "S0", "persona": "P1", "model": "m-spec", "weight": 6}
            ],
            "default": {"model": "def"}
        }
        db.upsert_script_profile(tenant, "binding", "binding_default", "v1", json.dumps(binding), True)
        stager = StageAgentRuntime(tenant)
        
        # Case A: Persona P2 -> Matches Rule 1 only
        state = {"current_stage": "S0", "persona_id": "P2"}
        dec = stager.resolve_binding(state, {})
        self.assertEqual(dec.get("model"), "m-gen")
        
        # Case B: Persona P1 -> Matches Rule 1 (score 15) and Rule 2 (score 16)
        state = {"current_stage": "S0", "persona_id": "P1"}
        dec = stager.resolve_binding(state, {})
        self.assertEqual(dec.get("model"), "m-spec")


if __name__ == "__main__":
    unittest.main()
