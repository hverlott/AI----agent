
import sqlite3
import os
from database import DatabaseManager

def test_db():
    if os.path.exists("data/core.db"):
        print("Using existing DB")
    
    db = DatabaseManager("data/core.db")
    
    # 1. Insert a test record
    print("Inserting test record...")
    db.record_message_event(
        tenant_id="default",
        platform="telegram",
        chat_id="123456",
        direction="outbound",
        status="sent",
        tokens_used=100,
        model="test-model",
        cost=0.001,
        stage="test-stage",
        user_content="Test User Content",
        bot_response="Test Bot Response"
    )
    
    # 2. Retrieve it
    print("Retrieving records...")
    rows = db.list_message_events(tenant_id="default", limit=5)
    
    found = False
    for r in rows:
        print(f"ID: {r['id']}, Content: {r.get('user_content')}, Response: {r.get('bot_response')}")
        if r.get('user_content') == "Test User Content":
            found = True
            
    if found:
        print("SUCCESS: Record found with correct content.")
    else:
        print("FAILURE: Record not found or content empty.")

if __name__ == "__main__":
    test_db()
