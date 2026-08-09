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
    db_file = tmp_path / "test_wf_inspect_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up valid agents and workflow repository in temporary DB with dependency overrides."""
    agent_repo = SQLiteAgentRepository(temp_db)
    workflow_repo = SQLiteWorkflowRepository(temp_db)

    agent1 = agent_repo.save_agent("agent-inspect-1", "NOVA", "AI & Emerging Tech")
    agent2 = agent_repo.save_agent("agent-inspect-2", "ORION", "Cybersecurity")

    def override_get_agent_repository():
        return agent_repo

    def override_get_workflow_repository():
        return workflow_repo

    app.dependency_overrides[get_agent_repository] = override_get_agent_repository
    app.dependency_overrides[get_workflow_repository] = override_get_workflow_repository

    client = TestClient(app)
    yield agent1, agent2, client, workflow_repo
    app.dependency_overrides.clear()


def test_get_workflow_inspection_endpoint_success(setup_agent):
    """1. Test GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection returns 200 with full observability breakdown."""
    agent1, _, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult(
        workflow_id="wf-inspect-succ-001",
        agent_id=agent1.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="2026-08-09T00:00:00+00:00",
        completed_at="2026-08-09T00:00:08.500000+00:00",
        stages=[
            WorkflowStageResult("topic_discovery", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "Discovered topics"),
            WorkflowStageResult("editorial_evaluation", WorkflowStageStatus.SUCCEEDED, "t1", "t2", True, "Evaluated topics"),
            WorkflowStageResult("research", WorkflowStageStatus.SUCCEEDED, "t2", "t3", True, "Researched topics"),
        ],
        selected_topic_ids=["top-1"],
        research_ids=["res-1"],
        draft_ids=["draft-1"],
        publication_ids=["pub-1"],
        is_successful=True,
        halted_at_stage=None,
        rationale="Completed 3 stages",
        traceability={
            "top-1": {
                "topic_id": "top-1",
                "title": "Quantum AI",
                "research_id": "res-1",
                "draft_id": "draft-1",
                "publication_id": "pub-1",
                "is_publishable": True,
                "finding_ids": ["f1"],
                "claim_ids": ["c1"],
            }
        },
    )
    workflow_repo.save_workflow(wf)

    response = client.get(f"/api/agent/{agent1.agent_id}/workflow/wf-inspect-succ-001/inspection")
    assert response.status_code == 200
    data = response.json()

    assert data["workflow_id"] == "wf-inspect-succ-001"
    assert data["agent_id"] == agent1.agent_id
    assert data["status"] == WorkflowStatus.SUCCESS
    assert data["duration_seconds"] == 8.5
    assert data["is_successful"] is True
    assert data["selected_topic_count"] == 1
    assert data["research_count"] == 1
    assert data["draft_count"] == 1
    assert data["publication_count"] == 1

    stats = data["stage_stats"]
    assert stats["total_stages"] == 3
    assert stats["succeeded_stages"] == 3
    assert stats["failed_stages"] == 0

    trace_sum = data["traceability_summary"]
    assert "top-1" in trace_sum
    assert trace_sum["top-1"]["title"] == "Quantum AI"
    assert trace_sum["top-1"]["finding_count"] == 1


def test_get_workflow_inspection_failed_workflow(setup_agent):
    """2. Test GET workflow inspection endpoint for a failed workflow execution."""
    agent1, _, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult(
        workflow_id="wf-inspect-failed-001",
        agent_id=agent1.agent_id,
        status=WorkflowStatus.FAILED,
        started_at="2026-08-09T00:00:00+00:00",
        completed_at="2026-08-09T00:00:02+00:00",
        stages=[
            WorkflowStageResult("topic_discovery", WorkflowStageStatus.FAILED, "t0", "t1", False, "Discovery network error")
        ],
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=False,
        halted_at_stage="topic_discovery",
        rationale="Discovery error halted execution",
    )
    workflow_repo.save_workflow(wf)

    response = client.get(f"/api/agent/{agent1.agent_id}/workflow/wf-inspect-failed-001/inspection")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == WorkflowStatus.FAILED
    assert data["is_successful"] is False
    assert data["halted_at_stage"] == "topic_discovery"
    assert data["stage_stats"]["failed_stages"] == 1


def test_get_workflow_inspection_404_validations(setup_agent):
    """3. Test 404 responses for unknown agent, unknown workflow ID, and cross-agent mismatch."""
    agent1, agent2, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult("wf-agent1-only", agent1.agent_id, WorkflowStatus.SUCCESS, "t0", "t1", [], [], [], [], [], True, None, "Ok")
    workflow_repo.save_workflow(wf)

    # Unknown agent
    r1 = client.get("/api/agent/unknown-agent/workflow/wf-agent1-only/inspection")
    assert r1.status_code == 404

    # Unknown workflow
    r2 = client.get(f"/api/agent/{agent1.agent_id}/workflow/unknown-wf/inspection")
    assert r2.status_code == 404

    # Cross-agent mismatch
    r3 = client.get(f"/api/agent/{agent2.agent_id}/workflow/wf-agent1-only/inspection")
    assert r3.status_code == 404


def test_history_endpoint_status_filtering(setup_agent):
    """4. Test GET /api/agent/{agent_id}/workflows?status=... filter parameter."""
    agent1, _, client, workflow_repo = setup_agent

    workflow_repo.save_workflow(AgentWorkflowResult("wf-succ", agent1.agent_id, WorkflowStatus.SUCCESS, "2026-08-09T00:00:01Z", "t1", [], [], [], [], [], True, None, "Succ"))
    workflow_repo.save_workflow(AgentWorkflowResult("wf-nocont", agent1.agent_id, WorkflowStatus.NO_CONTENT, "2026-08-09T00:00:02Z", "t1", [], [], [], [], [], True, None, "No cont"))
    workflow_repo.save_workflow(AgentWorkflowResult("wf-failed", agent1.agent_id, WorkflowStatus.FAILED, "2026-08-09T00:00:03Z", "t1", [], [], [], [], [], False, "stg", "Fail"))

    response = client.get(f"/api/agent/{agent1.agent_id}/workflows?status=NO_CONTENT")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["workflow_id"] == "wf-nocont"


def test_history_endpoint_successful_boolean_filtering(setup_agent):
    """5. Test GET /api/agent/{agent_id}/workflows?successful=true and ?successful=false filter parameters."""
    agent1, _, client, workflow_repo = setup_agent

    workflow_repo.save_workflow(AgentWorkflowResult("wf-succ1", agent1.agent_id, WorkflowStatus.SUCCESS, "2026-08-09T00:00:01Z", "t1", [], [], [], [], [], True, None, "Succ"))
    workflow_repo.save_workflow(AgentWorkflowResult("wf-fail1", agent1.agent_id, WorkflowStatus.FAILED, "2026-08-09T00:00:02Z", "t1", [], [], [], [], [], False, "stg", "Fail"))

    r_true = client.get(f"/api/agent/{agent1.agent_id}/workflows?successful=true")
    assert r_true.status_code == 200
    d_true = r_true.json()
    assert d_true["total"] == 1
    assert d_true["items"][0]["workflow_id"] == "wf-succ1"

    r_false = client.get(f"/api/agent/{agent1.agent_id}/workflows?successful=false")
    assert r_false.status_code == 200
    d_false = r_false.json()
    assert d_false["total"] == 1
    assert d_false["items"][0]["workflow_id"] == "wf-fail1"


def test_inspection_and_history_endpoints_are_idempotent(setup_agent):
    """6. Test that GET inspection and history endpoints never mutate database state."""
    agent1, _, client, workflow_repo = setup_agent

    wf = AgentWorkflowResult("wf-idem-002", agent1.agent_id, WorkflowStatus.SUCCESS, "t0", "t1", [], [], [], [], [], True, None, "Idem")
    workflow_repo.save_workflow(wf)

    initial_count = workflow_repo.count_workflows_by_agent(agent1.agent_id)

    client.get(f"/api/agent/{agent1.agent_id}/workflow/wf-idem-002/inspection")
    client.get(f"/api/agent/{agent1.agent_id}/workflows?status=SUCCESS")
    client.get(f"/api/agent/{agent1.agent_id}/workflows?successful=true")

    final_count = workflow_repo.count_workflows_by_agent(agent1.agent_id)
    assert initial_count == final_count
