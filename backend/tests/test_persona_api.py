from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLitePersonaRepository,
    SQLitePostRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
    get_agent_repository,
    get_persona_repository,
    get_post_repository,
    get_workflow_repository,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_persona_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent and topic in temporary DB with FastAPI dependency overrides."""
    agent_repo = SQLiteAgentRepository(temp_db)
    persona_repo = SQLitePersonaRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)
    post_repo = SQLitePostRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)

    agent = agent_repo.save_agent("agent-api-per-test", "NOVA", "AI & Emerging Tech")
    topic = topic_repo.create_topic("top-api-per-001", agent.agent_id, "AI Persona Alignment Engine", "Desc", "https://example.com/api-per", "Tech")

    app.dependency_overrides[get_agent_repository] = lambda: agent_repo
    app.dependency_overrides[get_persona_repository] = lambda: persona_repo
    app.dependency_overrides[get_workflow_repository] = lambda: wf_repo
    app.dependency_overrides[get_post_repository] = lambda: post_repo

    client = TestClient(app)
    yield agent, topic, client, persona_repo, topic_repo
    app.dependency_overrides.clear()


def test_api_get_and_put_persona(setup_agent):
    """14-15. Test GET and PUT /api/agent/{agent_id}/persona."""
    agent, _, client, _, _ = setup_agent

    # 1. GET default persona
    get_res = client.get(f"/api/agent/{agent.agent_id}/persona")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["persona_name"] == "NOVA"
    assert get_data["primary_domain"] == "AI & Emerging Tech"

    # 2. PUT custom persona
    put_res = client.put(
        f"/api/agent/{agent.agent_id}/persona",
        json={
            "persona_name": "NOVA Tech Strategist",
            "primary_domain": "AI & Emerging Tech",
            "persona_description": "Senior Tech Strategist Persona",
            "secondary_domains": ["Robotics"],
            "preferred_keywords": ["agent", "llm"],
            "excluded_keywords": ["crypto"],
            "min_relevance_threshold": 0.6,
        }
    )
    assert put_res.status_code == 200
    put_data = put_res.json()
    assert put_data["persona_name"] == "NOVA Tech Strategist"
    assert put_data["min_relevance_threshold"] == 0.6

    # Re-GET to verify persistence
    re_get = client.get(f"/api/agent/{agent.agent_id}/persona")
    assert re_get.status_code == 200
    assert re_get.json()["persona_name"] == "NOVA Tech Strategist"


def test_api_persona_validation_errors(setup_agent):
    """6. Test Pydantic validation errors on PUT /persona (empty name or threshold > 1.0)."""
    agent, _, client, _, _ = setup_agent

    res_empty = client.put(
        f"/api/agent/{agent.agent_id}/persona",
        json={"persona_name": "   ", "primary_domain": "Tech"}
    )
    assert res_empty.status_code == 422

    res_thresh = client.put(
        f"/api/agent/{agent.agent_id}/persona",
        json={"persona_name": "NOVA", "primary_domain": "Tech", "min_relevance_threshold": 1.5}
    )
    assert res_thresh.status_code == 422


def test_api_unknown_agent_returns_404(setup_agent):
    """16. Test GET and PUT persona/feed config on non-existent agent returns HTTP 404."""
    _, _, client, _, _ = setup_agent

    get_res = client.get("/api/agent/agent-nonexistent/persona")
    assert get_res.status_code == 404

    put_res = client.put(
        "/api/agent/agent-nonexistent/persona",
        json={"persona_name": "Name", "primary_domain": "Tech"}
    )
    assert put_res.status_code == 404


def test_api_get_and_put_feed_config(setup_agent):
    """17-18. Test GET and PUT /api/agent/{agent_id}/feed/config."""
    agent, _, client, _, _ = setup_agent

    # 1. GET feed config
    get_res = client.get(f"/api/agent/{agent.agent_id}/feed/config")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["agent_id"] == agent.agent_id

    # 2. PUT feed config
    put_res = client.put(
        f"/api/agent/{agent.agent_id}/feed/config",
        json={
            "max_topics": 3,
            "min_relevance_score": 0.65,
            "allowed_categories": ["AI", "Tech"],
            "excluded_categories": ["Gambling"],
            "preferred_keywords": ["autonomous"],
            "excluded_keywords": ["spam"],
        }
    )
    assert put_res.status_code == 200
    put_data = put_res.json()
    assert put_data["min_relevance_score"] == 0.65
    assert put_data["preferred_keywords"] == ["autonomous"]


def test_workflow_persona_alignment_stage_and_traceability(setup_agent):
    """21-22. Test that workflow execution includes persona_alignment stage and traceability rationale."""
    agent, topic, client, _, _ = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert res.status_code == 200
    data = res.json()
    stage_names = [st["stage_name"] for st in data["stages"]]
    assert "persona_alignment" in stage_names
    assert "persona_alignment" in data["traceability"]
