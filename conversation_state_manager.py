from typing import Dict
from database import db
from datetime import datetime

class ConversationStateManager:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    def get_state(self, platform: str, user_id: str) -> Dict:
        s = db.get_conversation_state(self.tenant_id, platform, user_id)
        if s:
            return s
        return {
            "user_id": user_id,
            "platform": platform,
            "current_stage": "S0",
            "persona_id": "calm_professional",
            "intent_score": 0.0,
            "risk_level": "unknown",
            "slots": {},
            "handoff_required": False,
            "updated_at": datetime.now().isoformat()
        }
    def update_state(self, platform: str, user_id: str, state: Dict):
        db.upsert_conversation_state(self.tenant_id, platform, user_id, state)
    
    def delete_state(self, platform: str, user_id: str):
        db.delete_conversation_state(self.tenant_id, platform, user_id)
