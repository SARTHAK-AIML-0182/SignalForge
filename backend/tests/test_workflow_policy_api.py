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
    db_file = tmp_path / "test_policy_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent and topic in temporary DB with FastAPI dependency overrides."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)

    agent = agent_repo.save_agent("agent-api-pol-test", "NOVA", "AI & Emerging Tech")
    topic = topic_repo.create_topic("top-api-pol-001", agent.agent_id, "Quantum Computing Policy", "Desc", "https://example.com/api-pol", "Tech")

    app.dependency_overrides[get_agent_repository] = lambda: agent_repo
    app.dependency_overrides[get_workflow_repository] = lambda: wf_repo

    client = TestClient(app)
    yield agent, topic, client, wf_repo
    app.dependency_overrides.clear()


def test_api_default_policy_execution(setup_agent):
    """1. Test POST workflow run with default payload returns HTTP 200 and default policy."""
    agent, topic, client, _ = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["policy"] is not None
    assert data["policy"]["max_topics"] == 5
    assert data["policy"]["publication_mode"] == "dry_run"


def test_api_custom_valid_policy_execution(setup_agent):
    """2. Test POST workflow run with custom valid parameters returns HTTP 200 and effective custom policy."""
    agent, topic, client, _ = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={
                "max_topics": 3,
                "editorial_threshold": 0.75,
                "enable_dry_run_publication": True,
                "publication_mode": "dry_run",
            }
        )

    assert res.status_code == 200
    data = res.json()
    assert data["policy"] is not None
    assert data["policy"]["max_topics"] == 3
    assert data["policy"]["editorial_threshold"] == 7.5
    assert data["policy"]["publication_mode"] == "dry_run"


def test_api_invalid_max_topics_returns_422(setup_agent):
    """3. Test POST workflow run with invalid max_topics (0 or 99) returns HTTP 422."""
    agent, topic, client, wf_repo = setup_agent

    res_zero = client.post(
        f"/api/agent/{agent.agent_id}/workflow/run",
        json={"max_topics": 0}
    )
    res_over = client.post(
        f"/api/agent/{agent.agent_id}/workflow/run",
        json={"max_topics": 99}
    )

    assert res_zero.status_code == 422
    assert res_over.status_code == 422

    # Confirm 0 records were written
    assert wf_repo.count_workflows_by_agent(agent.agent_id) == 0


def test_api_invalid_publication_mode_returns_422(setup_agent):
    """4. Test POST workflow run with unsupported publication_mode ('live' / 'social') returns HTTP 422."""
    agent, topic, client, _ = setup_agent

    res = client.post(
        f"/api/agent/{agent.agent_id}/workflow/run",
        json={"publication_mode": "live"}
    )

    assert res.status_code == 422
    assert "publication_mode" in res.text.lower()


def test_api_get_workflow_and_inspection_returns_effective_policy(setup_agent):
    """5. Test GET workflow status, inspection, and history endpoints return stored effective policy."""
    agent, topic, client, _ = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        run_res = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"max_topics": 2, "editorial_threshold": 0.6}
        )
        assert run_res.status_code == 200
        wf_id = run_res.json()["workflow_id"]

        get_res = client.get(f"/api/agent/{agent.agent_id}/workflow/{wf_id}")
        insp_res = client.get(f"/api/agent/{agent.agent_id}/workflow/{wf_id}/inspection")
        list_res = client.get(f"/api/agent/{agent.agent_id}/workflows")

    assert get_res.status_code == 200
    assert get_res.json()["policy"]["max_topics"] == 2

    assert insp_res.status_code == 200
    assert insp_res.json()["policy"]["max_topics"] == 2

    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) == 1
    assert list_res.json()["items"][0]["policy"]["max_topics"] == 2
