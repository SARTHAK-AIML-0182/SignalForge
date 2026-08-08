import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.main import app
from app.repositories.agent_repository import SQLiteAgentRepository, get_agent_repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Fixture to override agent repository with an isolated temp database for each test."""
    test_db = tmp_path / "test_agent_init.db"
    init_db(test_db)
    test_repo = SQLiteAgentRepository(test_db)
    app.dependency_overrides[get_agent_repository] = lambda: test_repo
    yield test_repo
    app.dependency_overrides.clear()


def test_init_agent_success(setup_test_db):
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

    # Verify state saved in temporary SQLite repository
    stored_agent = setup_test_db.get_agent(data["agentId"])
    assert stored_agent is not None
    assert stored_agent.name == "NOVA"
    assert stored_agent.domain == "AI & Emerging Technology"
    assert stored_agent.status == "active"
    assert stored_agent.initialized_at is not None


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
