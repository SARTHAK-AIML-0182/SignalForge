import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteWorkflowRepository,
)
from app.repositories.workflow_repository import (
    calculate_duration_seconds,
    calculate_stage_stats,
    extract_traceability_summary,
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
    db_file = tmp_path / "test_obs_repo.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent in temporary DB."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-obs-test", "NOVA", "AI & Emerging Tech")
    return agent, temp_db


def test_calculate_duration_seconds():
    """1. Test execution duration calculation for valid ISO timestamps and incomplete/invalid inputs."""
    d1 = calculate_duration_seconds("2026-08-09T00:00:00+00:00", "2026-08-09T00:00:10.500000+00:00")
    assert d1 == 10.5

    d2 = calculate_duration_seconds("2026-08-09T00:00:00Z", "")
    assert d2 is None

    d3 = calculate_duration_seconds("invalid", "invalid")
    assert d3 is None


def test_calculate_stage_stats():
    """2. Test deterministic stage status statistics calculation."""
    stages = [
        WorkflowStageResult("s1", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "ok"),
        WorkflowStageResult("s2", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "ok"),
        WorkflowStageResult("s3", WorkflowStageStatus.FAILED, "t0", "t1", False, "err"),
        WorkflowStageResult("s4", WorkflowStageStatus.SKIPPED, "t0", "t1", True, "skip"),
        WorkflowStageResult("s5", WorkflowStageStatus.BLOCKED, "t0", "t1", False, "block"),
        WorkflowStageResult("s6", WorkflowStageStatus.RUNNING, "t0", "t1", False, "run"),
    ]
    stats = calculate_stage_stats(stages)

    assert stats["total_stages"] == 6
    assert stats["succeeded_stages"] == 2
    assert stats["failed_stages"] == 1
    assert stats["skipped_stages"] == 1
    assert stats["blocked_stages"] == 1
    assert stats["running_stages"] == 1


def test_extract_traceability_summary():
    """3. Test concise 9-stage traceability summary extraction."""
    traceability = {
        "top-1": {
            "topic_id": "top-1",
            "title": "Topic 1 Title",
            "research_id": "res-1",
            "draft_id": "draft-1",
            "publication_id": "pub-1",
            "is_publishable": True,
            "finding_ids": ["f1", "f2", "f3"],
            "claim_ids": ["c1", "c2"],
        }
    }
    summary = extract_traceability_summary(traceability)

    assert "top-1" in summary
    node = summary["top-1"]
    assert node["title"] == "Topic 1 Title"
    assert node["research_id"] == "res-1"
    assert node["draft_id"] == "draft-1"
    assert node["publication_id"] == "pub-1"
    assert node["is_publishable"] is True
    assert node["finding_count"] == 3
    assert node["claim_count"] == 2


def test_filtered_workflow_listing_by_status(setup_agent):
    """4. Test filtering workflow repository list by status (SUCCESS vs FAILED vs NO_CONTENT)."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    repo.save_workflow(AgentWorkflowResult("wf-1", agent.agent_id, WorkflowStatus.SUCCESS, "2026-08-09T00:00:01Z", "2026-08-09T00:00:02Z", [], [], [], [], [], True, None, "Succ"))
    repo.save_workflow(AgentWorkflowResult("wf-2", agent.agent_id, WorkflowStatus.FAILED, "2026-08-09T00:00:03Z", "2026-08-09T00:00:04Z", [], [], [], [], [], False, "stage_x", "Err"))
    repo.save_workflow(AgentWorkflowResult("wf-3", agent.agent_id, WorkflowStatus.SUCCESS, "2026-08-09T00:00:05Z", "2026-08-09T00:00:06Z", [], [], [], [], [], True, None, "Succ 2"))

    succ_list = repo.list_workflows_by_agent(agent.agent_id, status=WorkflowStatus.SUCCESS)
    assert len(succ_list) == 2
    assert succ_list[0].workflow_id == "wf-3"
    assert succ_list[1].workflow_id == "wf-1"

    failed_list = repo.list_workflows_by_agent(agent.agent_id, status=WorkflowStatus.FAILED)
    assert len(failed_list) == 1
    assert failed_list[0].workflow_id == "wf-2"

    assert repo.count_workflows_by_agent(agent.agent_id, status=WorkflowStatus.SUCCESS) == 2
    assert repo.count_workflows_by_agent(agent.agent_id, status=WorkflowStatus.FAILED) == 1


def test_filtered_workflow_listing_by_is_successful_boolean(setup_agent):
    """5. Test filtering workflow repository list by is_successful boolean flag."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    repo.save_workflow(AgentWorkflowResult("wf-succ", agent.agent_id, WorkflowStatus.SUCCESS, "t0", "t1", [], [], [], [], [], True, None, "Ok"))
    repo.save_workflow(AgentWorkflowResult("wf-fail", agent.agent_id, WorkflowStatus.FAILED, "t0", "t1", [], [], [], [], [], False, "stg", "Fail"))

    succ_workflows = repo.list_workflows_by_agent(agent.agent_id, is_successful=True)
    assert len(succ_workflows) == 1
    assert succ_workflows[0].workflow_id == "wf-succ"

    fail_workflows = repo.list_workflows_by_agent(agent.agent_id, is_successful=False)
    assert len(fail_workflows) == 1
    assert fail_workflows[0].workflow_id == "wf-fail"


def test_deterministic_history_ordering(setup_agent):
    """6. Test stable deterministic ordering (started_at DESC, workflow_id DESC tie-breaker)."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    # Save multiple workflows with identical started_at timestamp
    repo.save_workflow(AgentWorkflowResult("wf-a", agent.agent_id, WorkflowStatus.SUCCESS, "2026-08-09T00:00:00Z", "t1", [], [], [], [], [], True, None, "A"))
    repo.save_workflow(AgentWorkflowResult("wf-b", agent.agent_id, WorkflowStatus.SUCCESS, "2026-08-09T00:00:00Z", "t1", [], [], [], [], [], True, None, "B"))

    results = repo.list_workflows_by_agent(agent.agent_id)
    assert len(results) == 2
    assert results[0].workflow_id == "wf-b"
    assert results[1].workflow_id == "wf-a"
