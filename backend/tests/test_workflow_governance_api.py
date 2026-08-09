from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
    get_agent_repository,
    get_workflow_repository,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_governance_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent and topic in temporary DB with FastAPI dependency overrides."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)

    agent = agent_repo.save_agent("agent-api-gov-test", "NOVA", "AI & Emerging Tech")
    topic = topic_repo.create_topic("top-api-gov-001", agent.agent_id, "Quantum Safety Policy", "Desc", "https://example.com/api-gov", "Tech")

    app.dependency_overrides[get_agent_repository] = lambda: agent_repo
    app.dependency_overrides[get_workflow_repository] = lambda: wf_repo

    client = TestClient(app)
    yield agent, topic, client, wf_repo
    app.dependency_overrides.clear()


def test_api_governance_approved_run(setup_agent):
    """1. Test POST workflow run with valid policy returns HTTP 200 and governance decision."""
    agent, topic, client, _ = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["governance"] is not None
    assert data["governance"]["allowed"] is True
    assert data["governance"]["execution_mode"] == "dry_run"
    assert data["governance"]["publication_allowed"] is True


def test_api_governance_disabled_publication_run(setup_agent):
    """2. Test POST workflow run with disabled publication mode returns HTTP 200 and governance decision."""
    agent, topic, client, _ = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"publication_mode": "disabled", "enable_dry_run_publication": False}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["governance"] is not None
    assert data["governance"]["allowed"] is True
    assert data["governance"]["execution_mode"] == "disabled"
    assert data["governance"]["publication_allowed"] is False


def test_api_governance_rejection_returns_422(setup_agent):
    """3. Test POST workflow run with rejected policy (publication_mode='live') returns HTTP 422."""
    agent, topic, client, wf_repo = setup_agent

    res = client.post(
        f"/api/agent/{agent.agent_id}/workflow/run",
        json={"publication_mode": "live"}
    )

    assert res.status_code == 422
    assert "publication_mode" in res.text.lower() or "governance" in res.text.lower()

    # Confirm 0 records were created
    assert wf_repo.count_workflows_by_agent(agent.agent_id) == 0


def test_api_get_workflow_and_inspection_exposes_governance(setup_agent):
    """4-6. Test GET status, inspection, and list endpoints return governance state."""
    agent, topic, client, _ = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        run_res = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"max_topics": 2}
        )
        assert run_res.status_code == 200
        wf_id = run_res.json()["workflow_id"]

        get_res = client.get(f"/api/agent/{agent.agent_id}/workflow/{wf_id}")
        insp_res = client.get(f"/api/agent/{agent.agent_id}/workflow/{wf_id}/inspection")
        list_res = client.get(f"/api/agent/{agent.agent_id}/workflows")

    assert get_res.status_code == 200
    assert get_res.json()["governance"]["allowed"] is True
    assert get_res.json()["governance"]["execution_mode"] == "dry_run"

    assert insp_res.status_code == 200
    assert insp_res.json()["governance"]["allowed"] is True
    assert insp_res.json()["governance"]["execution_mode"] == "dry_run"

    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) == 1
    assert list_res.json()["items"][0]["governance"]["allowed"] is True
