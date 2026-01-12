import os
import sqlite3
from database import DatabaseManager

# Use a test database to avoid messing with the real one
TEST_DB_PATH = "data/test_core.db"

if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

def test_record_message_event():
    print("Initializing DatabaseManager with test DB...")
    db = DatabaseManager(db_path=TEST_DB_PATH)
    
    print("Testing record_message_event...")
    try:
        db.record_message_event(
            tenant_id="test_tenant",
            platform="telegram",
            chat_id="12345",
            direction="outbound",
            status="sent",
            tokens_used=150,
            model="gpt-test",
            cost=0.0003,
            stage="initial_stage"
        )
        print("Successfully recorded message event.")
    except Exception as e:
        print(f"Failed to record message event: {e}")
        return

    print("Verifying data in DB...")
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM message_events")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(message_events)")
    columns = [info[1] for info in cursor.fetchall()]
    print(f"Columns: {columns}")
    
    for row in rows:
        row_dict = dict(zip(columns, row))
        print(f"Row: {row_dict}")
        
        assert row_dict['model'] == "gpt-test"
        assert row_dict['cost'] == 0.0003
        assert row_dict['stage'] == "initial_stage"
        assert row_dict['tokens_used'] == 150
        
    conn.close()
    print("Test passed!")

if __name__ == "__main__":
    test_record_message_event()
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
