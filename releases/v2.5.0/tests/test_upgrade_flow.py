import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.modules.orchestrator.runtime import StageAgentRuntime
from src.modules.orchestrator.supervisor import SupervisorAgent
from database import DatabaseManager
import json

# Mock DB
@pytest.fixture
def mock_db(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("src.modules.orchestrator.runtime.db", mock)
    monkeypatch.setattr("src.modules.orchestrator.supervisor.db", mock)
    return mock

@pytest.fixture
def stager():
    return StageAgentRuntime("test_tenant")

@pytest.fixture
def supervisor():
    return SupervisorAgent("test_tenant", {})

def test_build_system_prompt(stager, mock_db):
    # Setup Mock Data
    mock_db.get_script_profile_by_name.side_effect = lambda tenant, ptype, name, version=None: {
        "content": json.dumps({
            "description": f"{ptype} description",
            "style": "Friendly",
            "goal": "Sell stuff",
            "constraints": "No lies"
        })
    }
    
    state = {"current_stage": "S1", "persona_id": "sales"}
    base_prompt = "You are a bot."
    kb_items = []
    
    prompt = stager.build_system_prompt(state, base_prompt, kb_items)
    
    assert "You are a bot." in prompt
    assert "【当前人设 (sales)】" in prompt
    assert "Friendly" in prompt
    assert "【当前阶段 (S1)】" in prompt
    assert "Sell stuff" in prompt
    assert "No lies" in prompt

@pytest.mark.asyncio
async def test_supervisor_completion_check(supervisor, mock_db):
    # Setup Mock Stage with Completion Condition
    mock_db.get_script_profile_by_name.return_value = {
        "content": json.dumps({
            "completion_condition": "User says yes",
            "next_stage": "S2"
        })
    }
    
    # Mock AI Client
    mock_ai = MagicMock()
    mock_ai.chat.completions.create = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({
            "completion_met": True,
            "extracted_slots": {}
        })))]
    ))
    
    state = {"current_stage": "S1"}
    history = [{"role": "user", "content": "yes, I agree"}]
    
    decision = await supervisor.decide(state, history, ai_client=mock_ai, model_name="gpt-4")
    
    assert decision["advance_stage"] is True
    assert decision["next_stage"] == "S2"
    # Verify AI was called with prompt containing condition
    call_args = mock_ai.chat.completions.create.call_args
    assert "User says yes" in call_args[1]["messages"][0]["content"]

@pytest.mark.asyncio
async def test_supervisor_handoff(supervisor, mock_db):
    state = {"current_stage": "S1"}
    history = [{"role": "user", "content": "I need help, 转接人工"}]
    
    # Mock DB return empty or whatever, doesn't matter for handoff check which is regex based
    mock_db.get_script_profile_by_name.return_value = {}
    
    decision = await supervisor.decide(state, history)
    
    assert "handoff_requested" in decision["risk_flags"]

@pytest.mark.asyncio
async def test_supervisor_slot_extraction(supervisor, mock_db):
    # Setup Mock Stage with Slots
    mock_db.get_script_profile_by_name.return_value = {
        "content": json.dumps({
            "slots": ["email"],
            "completion_condition": "Email collected"
        })
    }
    
    # Mock AI Client
    mock_ai = MagicMock()
    mock_ai.chat.completions.create = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({
            "extracted_slots": {"email": "bob@test.com"},
            "completion_met": True
        })))]
    ))
    
    state = {"current_stage": "S1", "slots": {}}
    history = [{"role": "user", "content": "my email is bob@test.com"}]
    
    decision = await supervisor.decide(state, history, ai_client=mock_ai, model_name="gpt-4")
    
    assert decision["updated_slots"]["email"] == "bob@test.com"
    assert decision["advance_stage"] is True

