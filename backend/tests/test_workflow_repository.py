import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteWorkflowRepository,
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
    db_file = tmp_path / "test_wf_repo.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent in temporary DB."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-wf-repo-test", "NOVA", "AI & Emerging Tech")
    return agent, temp_db


def test_workflow_repository_creation_and_retrieval(setup_agent):
    """1. Test creating and retrieving a workflow record."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    wf = AgentWorkflowResult(
        workflow_id="wf-test-001",
        agent_id=agent.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="2026-08-09T00:00:00Z",
        completed_at="2026-08-09T00:00:05Z",
        stages=[
            WorkflowStageResult("topic_discovery", WorkflowStageStatus.SUCCEEDED, "2026-08-09T00:00:00Z", "2026-08-09T00:00:01Z", True, "Discovered 5 topics", {"topic_ids": ["t1"]})
        ],
        selected_topic_ids=["t1"],
        research_ids=["r1"],
        draft_ids=["d1"],
        publication_ids=["p1"],
        is_successful=True,
        halted_at_stage=None,
        rationale="Completed successfully",
        traceability={"t1": {"title": "Topic 1"}},
    )

    repo.save_workflow(wf)
    retrieved = repo.get_workflow("wf-test-001")

    assert retrieved is not None
    assert retrieved.workflow_id == "wf-test-001"
    assert retrieved.agent_id == agent.agent_id
    assert retrieved.status == WorkflowStatus.SUCCESS
    assert retrieved.is_successful is True
    assert len(retrieved.stages) == 1
    assert retrieved.stages[0].stage_name == "topic_discovery"
    assert retrieved.traceability["t1"]["title"] == "Topic 1"


def test_workflow_repository_update(setup_agent):
    """2. Test updating an existing workflow record (e.g. RUNNING -> SUCCESS)."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    wf_init = AgentWorkflowResult(
        workflow_id="wf-test-002",
        agent_id=agent.agent_id,
        status=WorkflowStatus.RUNNING,
        started_at="2026-08-09T00:00:00Z",
        completed_at="",
        stages=[],
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=False,
        halted_at_stage=None,
        rationale="Executing",
    )
    repo.save_workflow(wf_init)

    retrieved_init = repo.get_workflow("wf-test-002")
    assert retrieved_init.status == WorkflowStatus.RUNNING

    wf_final = AgentWorkflowResult(
        workflow_id="wf-test-002",
        agent_id=agent.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="2026-08-09T00:00:00Z",
        completed_at="2026-08-09T00:00:10Z",
        stages=[
            WorkflowStageResult("stage_1", WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, "Stage 1 OK")
        ],
        selected_topic_ids=["t1"],
        research_ids=["r1"],
        draft_ids=["d1"],
        publication_ids=["p1"],
        is_successful=True,
        halted_at_stage=None,
        rationale="All completed",
    )
    repo.save_workflow(wf_final)

    retrieved_final = repo.get_workflow("wf-test-002")
    assert retrieved_final.status == WorkflowStatus.SUCCESS
    assert retrieved_final.completed_at == "2026-08-09T00:00:10Z"
    assert len(retrieved_final.stages) == 1


def test_list_workflows_by_agent(setup_agent):
    """3. Test listing historical workflows for an agent ordered by started_at DESC."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    for i in range(5):
        wf = AgentWorkflowResult(
            workflow_id=f"wf-list-{i}",
            agent_id=agent.agent_id,
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
            rationale=f"Workflow {i}",
        )
        repo.save_workflow(wf)

    history = repo.list_workflows_by_agent(agent.agent_id, limit=3, offset=0)
    assert len(history) == 3
    assert history[0].workflow_id == "wf-list-4"
    assert history[1].workflow_id == "wf-list-3"
    assert history[2].workflow_id == "wf-list-2"

    count = repo.count_workflows_by_agent(agent.agent_id)
    assert count == 5


def test_stage_persistence_and_ordered_reconstruction(setup_agent):
    """4. Test that workflow stages are persisted and reconstructed in exact execution order."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    stage_names = [
        "topic_discovery", "editorial_evaluation", "research",
        "research_validation", "research_synthesis", "content_brief",
        "draft_generation", "publishability_check", "dry_run_publication"
    ]

    stages = [
        WorkflowStageResult(s_name, WorkflowStageStatus.SUCCEEDED, "t0", "t1", True, f"{s_name} rationale")
        for s_name in stage_names
    ]

    wf = AgentWorkflowResult(
        workflow_id="wf-stages-order",
        agent_id=agent.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="t0",
        completed_at="t1",
        stages=stages,
        selected_topic_ids=[],
        research_ids=[],
        draft_ids=[],
        publication_ids=[],
        is_successful=True,
        halted_at_stage=None,
        rationale="Order test",
    )
    repo.save_workflow(wf)

    retrieved = repo.get_workflow("wf-stages-order")
    assert retrieved is not None
    assert len(retrieved.stages) == 9
    for idx, expected_name in enumerate(stage_names):
        assert retrieved.stages[idx].stage_name == expected_name


def test_status_types_persistence(setup_agent):
    """5. Test persisting different workflow status outcomes (RUNNING, SUCCESS, PARTIAL_SUCCESS, NO_CONTENT, FAILED)."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    statuses = [
        (WorkflowStatus.RUNNING, False),
        (WorkflowStatus.SUCCESS, True),
        (WorkflowStatus.PARTIAL_SUCCESS, True),
        (WorkflowStatus.NO_CONTENT, True),
        (WorkflowStatus.FAILED, False),
    ]

    for idx, (st, is_succ) in enumerate(statuses):
        wf_id = f"wf-status-{idx}"
        wf = AgentWorkflowResult(
            workflow_id=wf_id,
            agent_id=agent.agent_id,
            status=st,
            started_at="t0",
            completed_at="t1",
            stages=[],
            selected_topic_ids=[],
            research_ids=[],
            draft_ids=[],
            publication_ids=[],
            is_successful=is_succ,
            halted_at_stage="stage_x" if st == WorkflowStatus.FAILED else None,
            rationale=f"Status is {st}",
        )
        repo.save_workflow(wf)

        retrieved = repo.get_workflow(wf_id)
        assert retrieved.status == st
        assert retrieved.is_successful == is_succ


def test_traceability_dictionary_persistence(setup_agent):
    """6. Test that complex traceability mapping survives JSON round-tripping in repository."""
    agent, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    trace = {
        "top-100": {
            "topic_id": "top-100",
            "title": "Complex Trace",
            "research_id": "res-100",
            "finding_ids": ["f1", "f2"],
            "claim_ids": ["c1", "c2"],
            "draft_id": "draft-100",
            "is_publishable": True,
            "publication_id": "pub-100",
        }
    }

    wf = AgentWorkflowResult(
        workflow_id="wf-trace-json",
        agent_id=agent.agent_id,
        status=WorkflowStatus.SUCCESS,
        started_at="t0",
        completed_at="t1",
        stages=[],
        selected_topic_ids=["top-100"],
        research_ids=["res-100"],
        draft_ids=["draft-100"],
        publication_ids=["pub-100"],
        is_successful=True,
        halted_at_stage=None,
        rationale="Trace test",
        traceability=trace,
    )
    repo.save_workflow(wf)

    retrieved = repo.get_workflow("wf-trace-json")
    assert retrieved.traceability == trace
    assert retrieved.traceability["top-100"]["finding_ids"] == ["f1", "f2"]


def test_persistence_survives_repository_reinstantiation(setup_agent):
    """7. Test that persisted records survive repository re-instantiation against same DB path."""
    agent, db_path = setup_agent

    repo1 = SQLiteWorkflowRepository(db_path)
    wf = AgentWorkflowResult(
        workflow_id="wf-reinst-001",
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
        rationale="Survives reinstantiation",
    )
    repo1.save_workflow(wf)

    repo2 = SQLiteWorkflowRepository(db_path)
    retrieved = repo2.get_workflow("wf-reinst-001")
    assert retrieved is not None
    assert retrieved.workflow_id == "wf-reinst-001"
