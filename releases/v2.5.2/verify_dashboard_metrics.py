import os
import sys
import json
from src.core.business_core import BusinessCore
from src.core.database import db

def verify_dashboard_metrics():
    print(">>> Starting Dashboard Metrics Verification")
    
    # 1. Initialize BusinessCore
    tenant_id = "test_tenant_verify"
    bc = BusinessCore(tenant_id)
    print(f"Initialized BusinessCore for tenant: {tenant_id}")
    
    # 2. Insert some dummy data to ensure we have stats
    print("Inserting dummy message events...")
    db.record_message_event(
        tenant_id=tenant_id,
        platform="telegram",
        chat_id="verify_1",
        direction="outbound",
        status="sent",
        tokens_used=100,
        model="gpt-4",
        cost=0.003,
        stage="stage_intro"
    )
    db.record_message_event(
        tenant_id=tenant_id,
        platform="telegram",
        chat_id="verify_2",
        direction="outbound",
        status="sent",
        tokens_used=200,
        model="gpt-3.5-turbo",
        cost=0.0004,
        stage="stage_product"
    )
    db.record_message_event(
        tenant_id=tenant_id,
        platform="telegram",
        chat_id="verify_3",
        direction="outbound",
        status="sent",
        tokens_used=50,
        model="gpt-3.5-turbo",
        cost=0.0001,
        stage="stage_intro"
    )
    
    # 3. Fetch Dashboard Data
    print("Fetching dashboard data...")
    stats = bc.get_dashboard_data()
    
    # 4. Verify Metrics
    print("\n--- Verification Results ---")
    
    # Total Tokens
    total_tokens = stats.get("total_tokens", 0)
    print(f"Total Tokens: {total_tokens} (Expected >= 350)")
    if total_tokens >= 350:
        print("✅ Total Tokens Verification Passed")
    else:
        print("❌ Total Tokens Verification Failed")
        
    # Total Cost
    total_cost = stats.get("total_cost", 0.0)
    print(f"Total Cost: ${total_cost:.5f} (Expected >= 0.0035)")
    if total_cost >= 0.0035:
        print("✅ Total Cost Verification Passed")
    else:
        print("❌ Total Cost Verification Failed")
        
    # Cost by Stage
    cost_by_stage = stats.get("cost_by_stage", {})
    print(f"Cost by Stage: {json.dumps(cost_by_stage, indent=2)}")
    
    if "stage_intro" in cost_by_stage and "stage_product" in cost_by_stage:
        print("✅ Cost by Stage Verification Passed (Stages found)")
    else:
        print("❌ Cost by Stage Verification Failed (Missing stages)")
        
    print("\n>>> Verification Completed")

if __name__ == "__main__":
    verify_dashboard_metrics()
