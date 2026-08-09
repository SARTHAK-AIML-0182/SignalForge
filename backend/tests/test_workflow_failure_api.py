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
    db_file = tmp_path / "test_wf_failure_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up valid agent in temporary DB with FastAPI dependency overrides."""
    agent_repo = SQLiteAgentRepository(temp_db)
    workflow_repo = SQLiteWorkflowRepository(temp_db)

    agent = agent_repo.save_agent("agent-fail-api", "NOVA", "AI & Emerging Tech")

    def override_get_agent_repository():
        return agent_repo

    def override_get_workflow_repository():
        return workflow_repo

    app.dependency_overrides[get_agent_repository] = override_get_agent_repository
    app.dependency_overrides[get_workflow_repository] = override_get_workflow_repository

    client = TestClient(app)
    yield agent, client, workflow_repo
    app.dependency_overrides.clear()


def test_workflow_run_sanitized_500_on_top_level_exception(setup_agent):
    """1. Test POST /api/agent/{agent_id}/workflow/run returns HTTP 500 with sanitized detail on unexpected orchestrator exception."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow", side_effect=MemoryError("Out of memory in C:\\sqlite3\\data.db")):
        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})
        assert response.status_code == 500
        data = response.json()

        assert data["detail"] == "Internal workflow execution error."
        assert "MemoryError" not in response.text
        assert "sqlite3" not in response.text
        assert "data.db" not in response.text


def test_workflow_get_returns_persisted_failed_state(setup_agent):
    """2. Test GET /api/agent/{agent_id}/workflow/{workflow_id} returns persisted FAILED status and stages."""
    agent, client, workflow_repo = setup_agent

    failed_wf = AgentWorkflowResult(
        workflow_id="wf-failed-api-001",
        agent_id=agent.agent_id,
        status=WorkflowStatus.FAILED,
        started_at="2026-08-09T00:00:00Z",
        completed_at="2026-08-09T00:00:01Z",
        stages=[
            WorkflowStageResult("topic_discovery", WorkflowStageStatus.FAILED, "t0", "t1", False, "Discovery network timeout")
        ],
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=False,
        halted_at_stage="topic_discovery",
        rationale="Discovery network timeout halted execution.",
    )
    workflow_repo.save_workflow(failed_wf)

    response = client.get(f"/api/agent/{agent.agent_id}/workflow/wf-failed-api-001")
    assert response.status_code == 200
    data = response.json()

    assert data["workflow_id"] == "wf-failed-api-001"
    assert data["status"] == WorkflowStatus.FAILED
    assert data["is_successful"] is False
    assert data["halted_at_stage"] == "topic_discovery"
    assert len(data["stages"]) == 1
    assert data["stages"][0]["status"] == WorkflowStageStatus.FAILED


def test_workflow_inspection_reports_failed_stage_stats(setup_agent):
    """3. Test GET inspection endpoint reports correct stage stats and halted stage for failed workflow."""
    agent, client, workflow_repo = setup_agent

    failed_wf = AgentWorkflowResult(
        workflow_id="wf-failed-inspect-002",
        agent_id=agent.agent_id,
        status=WorkflowStatus.FAILED,
        started_at="2026-08-09T00:00:00Z",
        completed_at="2026-08-09T00:00:02Z",
        stages=[
            WorkflowStageResult("topic_discovery", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "Discovered 1 topic"),
            WorkflowStageResult("editorial_evaluation", WorkflowStageStatus.FAILED, "t1", "t2", False, "Editorial evaluation error"),
        ],
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=False,
        halted_at_stage="editorial_evaluation",
        rationale="Editorial error halted workflow.",
    )
    workflow_repo.save_workflow(failed_wf)

    response = client.get(f"/api/agent/{agent.agent_id}/workflow/wf-failed-inspect-002/inspection")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == WorkflowStatus.FAILED
    assert data["is_successful"] is False
    assert data["halted_at_stage"] == "editorial_evaluation"
    assert data["stage_stats"]["total_stages"] == 2
    assert data["stage_stats"]["succeeded_stages"] == 1
    assert data["stage_stats"]["failed_stages"] == 1


def test_get_endpoints_are_idempotent_and_non_duplicating(setup_agent):
    """4. Test that GET endpoints never duplicate workflow records or trigger workflow re-execution."""
    agent, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult(
        workflow_id="wf-idem-003",
        agent_id=agent.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="2026-08-09T00:00:00Z",
        completed_at="2026-08-09T00:00:01Z",
        stages=[],
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=True,
        halted_at_stage=None,
        rationale="Ok",
    )
    workflow_repo.save_workflow(wf)

    initial_count = workflow_repo.count_workflows_by_agent(agent.agent_id)

    client.get(f"/api/agent/{agent.agent_id}/workflow/wf-idem-003")
    client.get(f"/api/agent/{agent.agent_id}/workflow/wf-idem-003/inspection")
    client.get(f"/api/agent/{agent.agent_id}/workflows")

    final_count = workflow_repo.count_workflows_by_agent(agent.agent_id)
    assert initial_count == final_count == 1
