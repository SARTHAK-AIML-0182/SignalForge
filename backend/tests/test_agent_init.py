import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.agent_repository import get_agent_repository

client = TestClient(app)


def test_init_agent_success():
    """Test successful agent initialization with valid persona name and domain."""
    payload = {
        "persona": {
            "name": "NOVA",
            "domain": "AI & Emerging Technology"
        }
    }
    response = client.post("/api/agent/init", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "agentId" in data
    assert isinstance(data["agentId"], str)
    assert len(data["agentId"]) > 0

    # Verify state saved in repository
    repo = get_agent_repository()
    stored_agent = repo.get_agent(data["agentId"])
    assert stored_agent is not None
    assert stored_agent.name == "NOVA"
    assert stored_agent.domain == "AI & Emerging Technology"


def test_init_agent_missing_persona():
    """Test initialization failure when persona object is missing."""
    response = client.post("/api/agent/init", json={})
    assert response.status_code == 422


def test_init_agent_empty_persona_name():
    """Test initialization failure when persona name is empty or only whitespace."""
    payload = {
        "persona": {
            "name": "   ",
            "domain": "AI & Emerging Technology"
        }
    }
    response = client.post("/api/agent/init", json=payload)
    assert response.status_code == 422


def test_init_agent_empty_persona_domain():
    """Test initialization failure when persona domain is empty string."""
    payload = {
        "persona": {
            "name": "NOVA",
            "domain": ""
        }
    }
    response = client.post("/api/agent/init", json=payload)
    assert response.status_code == 422


def test_init_agent_missing_fields_in_persona():
    """Test failure when individual persona attributes are omitted."""
    # Missing name
    response_no_name = client.post("/api/agent/init", json={"persona": {"domain": "Tech"}})
    assert response_no_name.status_code == 422

    # Missing domain
    response_no_domain = client.post("/api/agent/init", json={"persona": {"name": "NOVA"}})
    assert response_no_domain.status_code == 422
