import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import db

class BusinessCore:
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        # Ensure tenant exists in DB
        self._ensure_tenant()

    def _ensure_tenant(self):
        config = db.get_tenant_config(self.tenant_id)
        if not config:
            db.upsert_tenant_config(self.tenant_id, self._default_config())

    def _default_config(self):
        return {
            "plan": "free",
            "status": "active",
            "subscription_end": (datetime.now() + timedelta(days=30)).isoformat(),
            "branding": {
                "company_name": "AI Talk",
                "logo_url": "",
                "theme_color": "#000000"
            },
            "features": {
                "max_bots": 1,
                "max_daily_messages": 100,
                "analytics_enabled": False,
                "white_label": False
            }
        }

    # --- Public API ---

    def get_subscription_info(self) -> Dict:
        config = db.get_tenant_config(self.tenant_id)
        if not config:
            # Fallback or re-init
            return self._default_config()
        return config

    def update_branding(self, name: str, theme: str):
        config = self.get_subscription_info()
        if "branding" not in config:
            config["branding"] = {}
        config["branding"]["company_name"] = name
        config["branding"]["theme_color"] = theme
        db.upsert_tenant_config(self.tenant_id, config)
        db.log_audit(self.tenant_id, "Admin", "update_branding", {"name": name})

    def upgrade_plan(self, plan_level: str):
        """Simulate plan upgrade logic"""
        config = self.get_subscription_info()
        plans = {
            "free": {"max_bots": 1, "max_daily_messages": 100, "analytics_enabled": False, "white_label": False},
            "pro": {"max_bots": 5, "max_daily_messages": 5000, "analytics_enabled": True, "white_label": False},
            "enterprise": {"max_bots": 999, "max_daily_messages": 999999, "analytics_enabled": True, "white_label": True}
        }
        
        if plan_level in plans:
            config["plan"] = plan_level
            config["features"] = plans[plan_level]
            # Extend for 1 year
            config["subscription_end"] = (datetime.now() + timedelta(days=365)).isoformat()
            db.upsert_tenant_config(self.tenant_id, config)
            db.log_audit(self.tenant_id, "Admin", "upgrade_plan", {"plan": plan_level})
            return True
        return False

    def get_dashboard_data(self) -> Dict:
        """
        Aggregate real data from DB for the dashboard.
        """
        # 1. Message Volume (Last 7 days)
        metrics = db.get_dashboard_metrics(self.tenant_id, days=7)
        msg_trend = metrics.get("message_trend", {})
        total_tokens = metrics.get("total_tokens", 0)
        total_cost = metrics.get("total_cost", 0.0)
        active_users = metrics.get("active_users", 0)
        cost_by_stage = metrics.get("cost_by_stage", {})
        
        # 2. Mock Funnel (Since we don't have real funnel event tracking hooked up yet)
        # In a real scenario, we would query `message_events` for specific tags
        funnel = {
            "visitors": 1000,
            "conversations": 450,
            "leads": 120,
            "deals": 15
        }

        return {
            "daily_messages": msg_trend,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "active_users": active_users,
            "cost_by_stage": cost_by_stage,
            "conversion_funnel": funnel,
            # Add more real-time stats
            "total_messages_today": msg_trend.get(datetime.now().strftime("%Y-%m-%d"), 0)
        }

    def record_event(self, event_type: str, details: Dict = None):
        """Track business events"""
        # For now, we log to audit, but in future this should go to a specialized events table
        db.log_audit(self.tenant_id, "System", "business_event", {"type": event_type, "details": details})
