from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.main import app
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteWorkflowRepository,
    get_agent_repository,
    get_workflow_repository,
)
from app.services.workflow.models import (
    AgentWorkflowResult,
    WorkflowStageResult,
    WorkflowStageStatus,
    WorkflowStatus,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_wf_status_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent and workflow repository in temporary DB with dependency overrides."""
    agent_repo = SQLiteAgentRepository(temp_db)
    workflow_repo = SQLiteWorkflowRepository(temp_db)

    agent1 = agent_repo.save_agent("agent-api-status-1", "NOVA", "AI & Emerging Tech")
    agent2 = agent_repo.save_agent("agent-api-status-2", "ORION", "Cybersecurity")

    def override_get_agent_repository():
        return agent_repo

    def override_get_workflow_repository():
        return workflow_repo

    app.dependency_overrides[get_agent_repository] = override_get_agent_repository
    app.dependency_overrides[get_workflow_repository] = override_get_workflow_repository

    client = TestClient(app)
    yield agent1, agent2, client, workflow_repo
    app.dependency_overrides.clear()


def test_get_workflow_status_by_id(setup_agent):
    """1. Test GET /api/agent/{agent_id}/workflow/{workflow_id} returns 200 with complete persisted state."""
    agent1, _, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult(
        workflow_id="wf-api-get-001",
        agent_id=agent1.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="2026-08-09T00:00:00Z",
        completed_at="2026-08-09T00:00:05Z",
        stages=[
            WorkflowStageResult("topic_discovery", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "Discovered 2", {"topic_ids": ["t1"]})
        ],
        selected_topic_ids=["t1"],
        research_ids=["r1"],
        draft_ids=["d1"],
        publication_ids=["p1"],
        is_successful=True,
        halted_at_stage=None,
        rationale="Success rationale",
        traceability={"t1": {"title": "Topic 1"}},
    )
    workflow_repo.save_workflow(wf)

    response = client.get(f"/api/agent/{agent1.agent_id}/workflow/wf-api-get-001")
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == "wf-api-get-001"
    assert data["agent_id"] == agent1.agent_id
    assert data["status"] == WorkflowStatus.SUCCESS
    assert data["is_successful"] is True
    assert len(data["stages"]) == 1
    assert data["stages"][0]["stage_name"] == "topic_discovery"
    assert data["traceability"]["t1"]["title"] == "Topic 1"


def test_get_workflow_status_unknown_agent_returns_404(setup_agent):
    """2. Test GET workflow status for unknown agent returns HTTP 404."""
    _, _, client, _ = setup_agent

    response = client.get("/api/agent/unknown-agent-id/workflow/wf-any")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_workflow_status_unknown_workflow_returns_404(setup_agent):
    """3. Test GET workflow status for unknown workflow ID returns HTTP 404."""
    agent1, _, client, _ = setup_agent

    response = client.get(f"/api/agent/{agent1.agent_id}/workflow/unknown-workflow-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_workflow_status_cross_agent_mismatch_returns_404(setup_agent):
    """4. Test GET workflow status returns 404 if workflow belongs to another agent."""
    agent1, agent2, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult(
        workflow_id="wf-agent1-only",
        agent_id=agent1.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="t0",
        completed_at="t1",
        stages=[],
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=True,
        halted_at_stage=None,
        rationale="Agent 1 workflow",
    )
    workflow_repo.save_workflow(wf)

    # Attempting to fetch agent1's workflow using agent2's agent_id
    response = client.get(f"/api/agent/{agent2.agent_id}/workflow/wf-agent1-only")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_workflows_history_endpoint(setup_agent):
    """5. Test GET /api/agent/{agent_id}/workflows returns paginated workflow summaries."""
    agent1, _, client, workflow_repo = setup_agent

    for i in range(3):
        wf = AgentWorkflowResult(
            workflow_id=f"wf-hist-{i}",
            agent_id=agent1.agent_id,
            status=WorkflowStatus.SUCCESS,
            started_at=f"2026-08-09T00:00:0{i}Z",
            completed_at=f"2026-08-09T00:00:0{i+1}Z",
            stages=[],
            selected_topic_ids=[f"t-{i}"],
            research_ids=[],
            draft_ids=[],
            publication_ids=[f"p-{i}"],
            is_successful=True,
            halted_at_stage=None,
            rationale=f"Hist {i}",
        )
        workflow_repo.save_workflow(wf)

    response = client.get(f"/api/agent/{agent1.agent_id}/workflows?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    # Verify summary fields
    first_item = data["items"][0]
    assert first_item["workflow_id"] == "wf-hist-2"
    assert first_item["selected_topic_ids_count"] == 1
    assert first_item["publication_ids_count"] == 1


def test_list_workflows_pagination_offset(setup_agent):
    """6. Test pagination offset parameter in workflows history endpoint."""
    agent1, _, client, workflow_repo = setup_agent

    for i in range(5):
        wf = AgentWorkflowResult(
            workflow_id=f"wf-offset-{i}",
            agent_id=agent1.agent_id,
            status=WorkflowStatus.SUCCESS,
            started_at=f"2026-08-09T00:00:0{i}Z",
            completed_at=f"2026-08-09T00:00:0{i+1}Z",
            stages=[],
            selected_topic_ids=[],
            research_ids=[],
            draft_ids=[],
            publication_ids=[],
            is_successful=True,
            halted_at_stage=None,
            rationale=f"Offset {i}",
        )
        workflow_repo.save_workflow(wf)

    response = client.get(f"/api/agent/{agent1.agent_id}/workflows?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["workflow_id"] == "wf-offset-2"


def test_get_requests_are_idempotent(setup_agent):
    """7. Test that GET status and history endpoints never mutate database records."""
    agent1, _, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult(
        workflow_id="wf-idem-001",
        agent_id=agent1.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="t0",
        completed_at="t1",
        stages=[],
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=True,
        halted_at_stage=None,
        rationale="Idem test",
    )
    workflow_repo.save_workflow(wf)

    initial_count = workflow_repo.count_workflows_by_agent(agent1.agent_id)

    # Perform multiple GET requests
    client.get(f"/api/agent/{agent1.agent_id}/workflow/wf-idem-001")
    client.get(f"/api/agent/{agent1.agent_id}/workflows")
    client.get(f"/api/agent/{agent1.agent_id}/workflow/wf-idem-001")

    final_count = workflow_repo.count_workflows_by_agent(agent1.agent_id)
    assert initial_count == final_count


def test_workflow_run_endpoint_persists_record_in_sqlite(setup_agent):
    """8. Test that calling POST /api/agent/{agent_id}/workflow/run automatically persists record in SQLite."""
    agent1, _, client, workflow_repo = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc:
        mock_disc.return_value = []

        response = client.post(f"/api/agent/{agent1.agent_id}/workflow/run", json={})

    assert response.status_code == 200
    wf_id = response.json()["workflow_id"]

    # Verify workflow was persisted in SQLite and can be retrieved via GET endpoint
    get_res = client.get(f"/api/agent/{agent1.agent_id}/workflow/{wf_id}")
    assert get_res.status_code == 200
    assert get_res.json()["workflow_id"] == wf_id
    assert get_res.json()["status"] == WorkflowStatus.NO_CONTENT
