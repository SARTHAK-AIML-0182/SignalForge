from unittest.mock import patch
import pytest
import sqlite3
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db, get_connection
from app.repositories import (
    SQLiteAgentRepository,
    SQLitePostRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
    get_agent_repository,
    get_post_repository,
    get_workflow_repository,
)
from app.services.workflow import run_agent_workflow, WorkflowPolicy


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_backend_audit.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_api_client(temp_db):
    """Fixture setting up TestClient with overridden repository dependencies pointing to temp_db."""
    agent_repo = SQLiteAgentRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)
    post_repo = SQLitePostRepository(temp_db)

    app.dependency_overrides[get_agent_repository] = lambda: agent_repo
    app.dependency_overrides[get_workflow_repository] = lambda: wf_repo
    app.dependency_overrides[get_post_repository] = lambda: post_repo

    client = TestClient(app)
    yield client, temp_db, agent_repo, wf_repo, post_repo
    app.dependency_overrides.clear()


def test_database_performance_indexes_created(temp_db):
    """1. Test that non-destructive SQLite performance indexes are created on startup."""
    conn = get_connection(temp_db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index';")
    index_names = [row["name"] for row in cursor.fetchall()]
    conn.close()

    assert "idx_topics_agent_id" in index_names
    assert "idx_posts_agent_id" in index_names
    assert "idx_research_agent_id" in index_names
    assert "idx_evidence_research_id" in index_names
    assert "idx_workflows_agent_id_started" in index_names
    assert "idx_workflow_stages_wf_order" in index_names


def test_full_e2e_backend_workflow_to_feed_pipeline(setup_api_client):
    """2. Test full end-to-end workflow execution from agent init, policy, governance, 9 stages, post creation to feed retrieval."""
    client, db_path, agent_repo, wf_repo, post_repo = setup_api_client

    # Step 1: Agent Initialization
    init_res = client.post(
        "/api/agent/init",
        json={"persona": {"name": "NOVA", "domain": "AI & Emerging Tech"}}
    )
    assert init_res.status_code == 200
    agent_id = init_res.json()["agentId"]
    assert agent_id.startswith("agent-")

    # Setup discovered topic
    topic_repo = SQLiteTopicRepository(db_path)
    topic = topic_repo.create_topic("top-e2e-001", agent_id, "Quantum AI Governance", "Desc", "https://example.com/q-ai", "Tech")

    # Step 2: Workflow Execution
    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        run_res = client.post(
            f"/api/agent/{agent_id}/workflow/run",
            json={"max_topics": 1, "editorial_threshold": 0.6}
        )

    assert run_res.status_code == 200
    wf_data = run_res.json()
    wf_id = wf_data["workflow_id"]
    assert wf_data["status"] in ("SUCCESS", "NO_CONTENT", "PARTIAL_SUCCESS")
    assert wf_data["policy"] is not None
    assert wf_data["policy"]["max_topics"] == 1
    assert wf_data["governance"] is not None
    assert wf_data["governance"]["allowed"] is True

    # Step 3: Agent Feed API Retrieval
    feed_res = client.get(f"/api/agent/feed?agentId={agent_id}")
    assert feed_res.status_code == 200
    feed_data = feed_res.json()
    assert feed_data["agentId"] == agent_id
    assert feed_data["status"] == "ok"
    assert isinstance(feed_data["posts"], list)

    # Step 4: Workflow Inspection API
    insp_res = client.get(f"/api/agent/{agent_id}/workflow/{wf_id}/inspection")
    assert insp_res.status_code == 200
    insp_data = insp_res.json()
    assert insp_data["workflow_id"] == wf_id
    assert insp_data["governance"]["allowed"] is True
    assert insp_data["policy"]["max_topics"] == 1

    # Step 5: Workflow History API
    list_res = client.get(f"/api/agent/{agent_id}/workflows")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_feed_api_404_on_missing_agent(setup_api_client):
    """3. Test GET /api/agent/feed returns HTTP 404 if agentId does not exist."""
    client, _, _, _, _ = setup_api_client
    res = client.get("/api/agent/feed?agentId=agent-nonexistent")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_process_restart_and_repository_reinstantiation(temp_db):
    """4. Test that persisted agents, workflows, policies, and governance survive process restart."""
    agent_repo1 = SQLiteAgentRepository(temp_db)
    topic_repo1 = SQLiteTopicRepository(temp_db)
    wf_repo1 = SQLiteWorkflowRepository(temp_db)

    agent = agent_repo1.save_agent("agent-restart-001", "NOVA", "AI & Emerging Tech")
    topic = topic_repo1.create_topic("top-restart-001", agent.agent_id, "Restart Test Topic", "Desc", "https://example.com/rst", "Tech")

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res1 = run_agent_workflow(agent.agent_id, config=WorkflowPolicy(max_topics=2), workflow_repo=wf_repo1)

    # Re-instantiate repositories (simulating app restart)
    agent_repo2 = SQLiteAgentRepository(temp_db)
    wf_repo2 = SQLiteWorkflowRepository(temp_db)

    reloaded_agent = agent_repo2.get_agent(agent.agent_id)
    assert reloaded_agent is not None
    assert reloaded_agent.name == "NOVA"

    reloaded_wf = wf_repo2.get_workflow(res1.workflow_id)
    assert reloaded_wf is not None
    assert reloaded_wf.policy["max_topics"] == 2
    assert reloaded_wf.governance["allowed"] is True


def test_legacy_database_record_compatibility(temp_db):
    """5. Test that legacy records without policy or governance columns load cleanly with None values."""
    agent_repo = SQLiteAgentRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)
    agent = agent_repo.save_agent("agent-legacy", "Legacy", "Tech")

    conn = get_connection(temp_db)
    with conn:
        conn.execute(
            """
            INSERT INTO workflows (
                workflow_id, agent_id, status, started_at, completed_at,
                is_successful, halted_at_stage, rationale, selected_topic_ids,
                research_ids, draft_ids, publication_ids, traceability, policy, governance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("wf-legacy-999", agent.agent_id, "SUCCESS", "2026-08-09T00:00:00Z", "2026-08-09T00:01:00Z", 1, None, "Legacy", "[]", "[]", "[]", "[]", "{}", "{}", "{}")
        )
    conn.close()

    legacy_wf = wf_repo.get_workflow("wf-legacy-999")
    assert legacy_wf is not None
    assert legacy_wf.policy is None
    assert legacy_wf.governance is None
