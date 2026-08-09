from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.main import app
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteTopicRepository,
    get_agent_repository,
)
from app.services.workflow.models import (
    AgentWorkflowResult,
    WorkflowConfig,
    WorkflowStageResult,
    WorkflowStageStatus,
    WorkflowStatus,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_wf_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent in temporary DB and overriding get_agent_repository."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-api-test", "NOVA", "AI & Emerging Tech")

    def override_get_agent_repository():
        return agent_repo

    app.dependency_overrides[get_agent_repository] = override_get_agent_repository
    client = TestClient(app)
    yield agent, client, agent_repo
    app.dependency_overrides.clear()


def test_successful_workflow_api_request(setup_agent):
    """1. Test successful workflow API request returns HTTP 200 and structured response."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-100",
            agent_id=agent.agent_id,
            status=WorkflowStatus.SUCCESS,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:05Z",
            stages=[
                WorkflowStageResult("topic_discovery", WorkflowStageStatus.SUCCEEDED, "2026-08-09T00:00:00Z", "2026-08-09T00:00:01Z", True, "Done")
            ],
            selected_topic_ids=["top-1"],
            research_ids=["res-1"],
            draft_ids=["draft-1"],
            publication_ids=["pub-1"],
            is_successful=True,
            halted_at_stage=None,
            rationale="Workflow completed",
            traceability={"top-1": {"title": "Topic 1"}},
        )

        response = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"max_topics": 2, "editorial_threshold": 0.70, "enable_dry_run_publication": True},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == "wf-api-100"
    assert data["agent_id"] == agent.agent_id
    assert data["status"] == WorkflowStatus.SUCCESS
    assert data["is_successful"] is True


def test_agent_not_found_returns_404(setup_agent):
    """2. Test that requesting workflow for non-existent agent returns HTTP 404."""
    _, client, _ = setup_agent

    response = client.post("/api/agent/non-existent-agent-id/workflow/run", json={})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_invalid_max_topics_returns_422(setup_agent):
    """3. Test that max_topics < 1 returns HTTP 422 validation error."""
    agent, client, _ = setup_agent

    response = client.post(
        f"/api/agent/{agent.agent_id}/workflow/run",
        json={"max_topics": 0},
    )
    assert response.status_code == 422


def test_invalid_editorial_threshold_returns_422(setup_agent):
    """4. Test that editorial_threshold outside [0.0, 1.0] returns HTTP 422 validation error."""
    agent, client, _ = setup_agent

    response = client.post(
        f"/api/agent/{agent.agent_id}/workflow/run",
        json={"editorial_threshold": 1.5},
    )
    assert response.status_code == 422

    response_neg = client.post(
        f"/api/agent/{agent.agent_id}/workflow/run",
        json={"editorial_threshold": -0.1},
    )
    assert response_neg.status_code == 422


def test_workflow_config_passed_correctly_to_orchestrator(setup_agent):
    """5. Test that API parameters map correctly to WorkflowConfig passed to orchestrator."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-101",
            agent_id=agent.agent_id,
            status=WorkflowStatus.SUCCESS,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:05Z",
            stages=[],
            selected_topic_ids=[],
            research_ids=[],
            draft_ids=[],
            publication_ids=[],
            is_successful=True,
            halted_at_stage=None,
            rationale="OK",
        )

        response = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"max_topics": 3, "editorial_threshold": 0.80, "enable_dry_run_publication": False},
        )

    assert response.status_code == 200
    mock_run.assert_called_once()
    passed_config = mock_run.call_args.kwargs["config"]
    assert passed_config.max_topics == 3
    assert abs(passed_config.editorial_threshold - 8.0) < 1e-5
    assert passed_config.enable_dry_run_publication is False


def test_workflow_result_serializes_correctly(setup_agent):
    """6. Test that workflow response serializes all required top-level JSON fields."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-102",
            agent_id=agent.agent_id,
            status=WorkflowStatus.SUCCESS,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:05Z",
            stages=[],
            selected_topic_ids=["t1"],
            research_ids=["r1"],
            draft_ids=["d1"],
            publication_ids=["p1"],
            is_successful=True,
            halted_at_stage=None,
            rationale="All good",
        )

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 200
    data = response.json()
    for field_name in [
        "workflow_id", "agent_id", "status", "started_at", "completed_at",
        "is_successful", "rationale", "selected_topic_ids", "research_ids",
        "draft_ids", "publication_ids", "stages", "traceability"
    ]:
        assert field_name in data


def test_stage_results_included_in_response(setup_agent):
    """7. Test that structured stage results are serialized in response."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-103",
            agent_id=agent.agent_id,
            status=WorkflowStatus.SUCCESS,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:05Z",
            stages=[
                WorkflowStageResult("topic_discovery", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "Discovered 5", {"topic_ids": ["t1"]}),
                WorkflowStageResult("editorial_evaluation", WorkflowStageStatus.SUCCEEDED, "t1", "t2", True, "Selected 1", {"selected_topic_ids": ["t1"]}),
            ],
            selected_topic_ids=["t1"],
            research_ids=[],
            draft_ids=[],
            publication_ids=[],
            is_successful=True,
            halted_at_stage=None,
            rationale="OK",
        )

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 200
    stages = response.json()["stages"]
    assert len(stages) == 2
    assert stages[0]["stage_name"] == "topic_discovery"
    assert stages[1]["stage_name"] == "editorial_evaluation"


def test_traceability_included_in_response(setup_agent):
    """8. Test that 9-stage end-to-end traceability map is serialized in response."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-104",
            agent_id=agent.agent_id,
            status=WorkflowStatus.SUCCESS,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:05Z",
            stages=[],
            selected_topic_ids=["top-x"],
            research_ids=["res-x"],
            draft_ids=["draft-x"],
            publication_ids=["pub-x"],
            is_successful=True,
            halted_at_stage=None,
            rationale="OK",
            traceability={
                "top-x": {
                    "topic_id": "top-x",
                    "title": "Trace Title",
                    "research_id": "res-x",
                    "draft_id": "draft-x",
                    "publication_id": "pub-x"
                }
            },
        )

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 200
    trace = response.json()["traceability"]
    assert "top-x" in trace
    assert trace["top-x"]["title"] == "Trace Title"


def test_controlled_no_content_response(setup_agent):
    """9. Test that controlled NO_CONTENT workflow result returns HTTP 200 with NO_CONTENT status."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-105",
            agent_id=agent.agent_id,
            status=WorkflowStatus.NO_CONTENT,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:02Z",
            stages=[
                WorkflowStageResult("editorial_evaluation", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "Zero topics selected")
            ],
            selected_topic_ids=[],
            research_ids=[],
            draft_ids=[],
            publication_ids=[],
            is_successful=True,
            halted_at_stage=None,
            rationale="Zero topics selected",
        )

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == WorkflowStatus.NO_CONTENT
    assert data["is_successful"] is True


def test_controlled_partial_success_response(setup_agent):
    """10. Test that controlled PARTIAL_SUCCESS workflow result returns HTTP 200."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-106",
            agent_id=agent.agent_id,
            status=WorkflowStatus.PARTIAL_SUCCESS,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:05Z",
            stages=[],
            selected_topic_ids=["t1", "t2"],
            research_ids=["r1"],
            draft_ids=["d1"],
            publication_ids=["p1"],
            is_successful=True,
            halted_at_stage=None,
            rationale="Topic 1 succeeded, Topic 2 failed",
        )

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == WorkflowStatus.PARTIAL_SUCCESS
    assert data["is_successful"] is True


def test_controlled_failed_result_represented_correctly(setup_agent):
    """11. Test that controlled FAILED workflow result returns HTTP 200 with FAILED status."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-107",
            agent_id=agent.agent_id,
            status=WorkflowStatus.FAILED,
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:01Z",
            stages=[
                WorkflowStageResult("topic_discovery", WorkflowStageStatus.FAILED, "t0", "t1", False, "Discovery crash")
            ],
            selected_topic_ids=[],
            research_ids=[],
            draft_ids=[],
            publication_ids=[],
            is_successful=False,
            halted_at_stage="topic_discovery",
            rationale="Discovery failed",
        )

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == WorkflowStatus.FAILED
    assert data["is_successful"] is False
    assert data["halted_at_stage"] == "topic_discovery"


def test_unexpected_internal_exception_produces_safe_500(setup_agent):
    """12. Test that unhandled workflow execution error returns HTTP 500."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.side_effect = RuntimeError("Database connection string error at C:\\secret\\db.sqlite")

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal workflow execution error."


def test_internal_exception_does_not_expose_stack_trace_or_paths(setup_agent):
    """13. Test that HTTP 500 detail does not contain stack traces or internal filesystem paths."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.side_effect = Exception("Internal Traceback (most recent call last): File 'app/db/secret.py', line 99")

        response = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={})

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "Traceback" not in detail
    assert "secret.py" not in detail
    assert detail == "Internal workflow execution error."


def test_dry_run_publication_configuration_respected(setup_agent):
    """14. Test that enable_dry_run_publication flag is passed to orchestrator config."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-108",
            agent_id=agent.agent_id,
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
            rationale="OK",
        )

        client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"enable_dry_run_publication": False},
        )

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["config"].enable_dry_run_publication is False


def test_api_does_not_invoke_real_publishing_adapters(setup_agent):
    """15. Test that API execution only uses dry-run workflow configuration and never real adapters."""
    agent, client, _ = setup_agent

    with patch("app.api.agent.run_agent_workflow") as mock_run:
        mock_run.return_value = AgentWorkflowResult(
            workflow_id="wf-api-109",
            agent_id=agent.agent_id,
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
            rationale="OK",
        )

        # Confirm API payload has no option to supply real publishing adapters
        response = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"max_topics": 1},
        )

    assert response.status_code == 200
    # Confirm publishing_adapter kwarg was not passed to run_agent_workflow by API route
    assert "publishing_adapter" not in mock_run.call_args.kwargs or mock_run.call_args.kwargs["publishing_adapter"] is None


def test_existing_agent_init_remains_functional(setup_agent):
    """16. Test that existing POST /api/agent/init endpoint remains fully functional."""
    _, client, _ = setup_agent

    response = client.post(
        "/api/agent/init",
        json={"persona": {"name": "APITester", "domain": "Cloud Security"}},
    )
    assert response.status_code == 200
    assert "agentId" in response.json()
    assert response.json()["agentId"].startswith("agent-")
