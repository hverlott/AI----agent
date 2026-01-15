import json

def test_whitelist_logic():
    print("Testing Whitelist Logic...")
    # Mock data
    groups = [
        {"id": 123, "title": "Valid Group"},
        {"title": "Invalid Group (No ID)"},
        {"id": 456, "title": "Another Valid Group"}
    ]
    
    # Logic from admin_multi.py
    valid_groups = [g for g in groups if g.get("id")]
    
    assert len(valid_groups) == 2
    assert valid_groups[0]["id"] == 123
    assert valid_groups[1]["id"] == 456
    print("✅ Whitelist filtering passed.")

def test_broadcast_logic():
    print("Testing Broadcast Logic...")
    # Mock data
    groups = [
        {"id": 101, "title": "G1"},
        {"title": "G2 (Bad)"},
        {"id": 103, "title": "G3"}
    ]
    loaded_groups = groups # Simulate loading from cache
    
    # Logic from admin_multi.py (render_telegram_broadcast)
    # 1. Filter valid
    valid_groups = [g for g in groups if g.get("id")]
    assert len(valid_groups) == 2
    
    # Simulate selection
    selected_ids = [101, 103]
    
    # Simulate sending loop
    results = []
    for cid in selected_ids:
        title = str(cid)
        for g in loaded_groups:
             # The fix: use .get("id")
            if g.get("id") == cid:
                title = g.get("title", str(cid))
                break
        results.append(title)
        
    assert "G1" in results
    assert "G3" in results
    print("✅ Broadcast sending loop passed.")

if __name__ == "__main__":
    test_whitelist_logic()
    test_broadcast_logic()
