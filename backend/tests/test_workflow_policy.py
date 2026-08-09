from unittest.mock import patch
import pytest

from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
)
from app.services.workflow import (
    WorkflowPolicy,
    resolve_workflow_policy,
    run_agent_workflow,
)
from app.services.workflow.models import AgentWorkflowResult, WorkflowStatus


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_policy.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent and topic in temporary DB."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    agent = agent_repo.save_agent("agent-pol-test", "NOVA", "AI & Emerging Tech")
    topic = topic_repo.create_topic("top-pol-001", agent.agent_id, "AI Policy Governance", "Desc", "https://example.com/pol", "Tech")
    return agent, topic, temp_db


def test_default_policy_creation():
    """1. Test default WorkflowPolicy creation and default values."""
    pol = WorkflowPolicy()
    assert pol.max_topics == 5
    assert pol.editorial_threshold == 0.65
    assert pol.enable_dry_run_publication is True
    assert pol.publication_mode == "dry_run"
    assert pol.max_topics_upper_bound == 10


def test_valid_max_topics():
    """2. Test valid max_topics bounds."""
    pol = WorkflowPolicy(max_topics=3).validate()
    assert pol.max_topics == 3

    pol_max = WorkflowPolicy(max_topics=10).validate()
    assert pol_max.max_topics == 10


def test_valid_editorial_threshold():
    """3. Test valid editorial_threshold values."""
    pol1 = WorkflowPolicy(editorial_threshold=0.5).validate()
    assert pol1.editorial_threshold == 0.5

    pol2 = WorkflowPolicy(editorial_threshold=8.0).validate()
    assert pol2.editorial_threshold == 8.0


def test_dry_run_publication_default():
    """4. Test dry-run publication default behavior."""
    pol = resolve_workflow_policy()
    assert pol.enable_dry_run_publication is True
    assert pol.publication_mode == "dry_run"


def test_max_topics_lower_bound_validation():
    """5. Test max_topics lower-bound validation (< 1 raises ValueError)."""
    with pytest.raises(ValueError, match="max_topics must be at least 1"):
        WorkflowPolicy(max_topics=0).validate()

    with pytest.raises(ValueError, match="max_topics must be at least 1"):
        WorkflowPolicy(max_topics=-2).validate()


def test_max_topics_upper_bound_validation():
    """6. Test max_topics upper-bound validation (> 10 raises ValueError)."""
    with pytest.raises(ValueError, match="max_topics cannot exceed safe maximum"):
        WorkflowPolicy(max_topics=11).validate()


def test_editorial_threshold_lower_bound_validation():
    """7. Test editorial_threshold lower-bound validation (< 0.0 raises ValueError)."""
    with pytest.raises(ValueError, match="editorial_threshold must be between"):
        WorkflowPolicy(editorial_threshold=-0.1).validate()


def test_editorial_threshold_upper_bound_validation():
    """8. Test editorial_threshold upper-bound validation (> 10.0 raises ValueError)."""
    with pytest.raises(ValueError, match="editorial_threshold must be between"):
        WorkflowPolicy(editorial_threshold=10.5).validate()


def test_invalid_publication_mode_rejection():
    """9. Test invalid publication mode rejection (e.g. 'live' or 'social')."""
    with pytest.raises(ValueError, match="Unsupported publication_mode"):
        WorkflowPolicy(publication_mode="live").validate()

    with pytest.raises(ValueError, match="Unsupported publication_mode"):
        WorkflowPolicy(publication_mode="social").validate()


def test_policy_serialization():
    """10. Test WorkflowPolicy to_dict() and from_dict() roundtrip."""
    pol = WorkflowPolicy(max_topics=7, editorial_threshold=0.8, publication_mode="disabled").validate()
    d = pol.to_dict()
    assert d["max_topics"] == 7
    assert d["editorial_threshold"] == 0.8
    assert d["publication_mode"] == "disabled"

    reconstructed = WorkflowPolicy.from_dict(d)
    assert reconstructed.max_topics == 7
    assert reconstructed.editorial_threshold == 0.8
    assert reconstructed.publication_mode == "disabled"


def test_policy_persistence_and_reinstantiation(setup_agent):
    """11-12. Test policy persistence in SQLite and survival after repository re-instantiation."""
    agent, topic, db_path = setup_agent
    repo1 = SQLiteWorkflowRepository(db_path)

    pol = WorkflowPolicy(max_topics=4, editorial_threshold=0.7)
    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = run_agent_workflow(agent.agent_id, config=pol, workflow_repo=repo1)

    assert res.policy is not None
    assert res.policy["max_topics"] == 4

    repo2 = SQLiteWorkflowRepository(db_path)
    fetched = repo2.get_workflow(res.workflow_id)
    assert fetched is not None
    assert fetched.policy is not None
    assert fetched.policy["max_topics"] == 4
    assert fetched.policy["editorial_threshold"] == 0.7


def test_workflow_result_and_get_expose_effective_policy(setup_agent):
    """13-14. Test that workflow execution result and GET workflow expose effective policy."""
    agent, topic, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = run_agent_workflow(agent.agent_id, workflow_repo=repo)

    assert res.policy is not None
    assert "max_topics" in res.policy
    assert "publication_mode" in res.policy

    fetched = repo.get_workflow(res.workflow_id)
    assert fetched.policy == res.policy


def test_invalid_policy_does_not_start_workflow_or_create_record(setup_agent):
    """15-16. Test that invalid policy raises ValueError before workflow starts and writes 0 DB records."""
    agent, topic, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    invalid_pol = WorkflowPolicy(max_topics=999)

    with pytest.raises(ValueError, match="max_topics cannot exceed safe maximum"):
        run_agent_workflow(agent.agent_id, config=invalid_pol, workflow_repo=repo)

    # Verify no workflow record was created in database
    workflows = repo.list_workflows_by_agent(agent.agent_id)
    assert len(workflows) == 0


def test_workflow_policy_immutability(setup_agent):
    """18. Test that persisted workflow policy remains immutable on repository GET requests."""
    agent, topic, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    pol = WorkflowPolicy(max_topics=2, editorial_threshold=0.6)
    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = run_agent_workflow(agent.agent_id, config=pol, workflow_repo=repo)

    fetched1 = repo.get_workflow(res.workflow_id)
    fetched2 = repo.get_workflow(res.workflow_id)
    assert fetched1.policy == fetched2.policy == pol.to_dict()


def test_legacy_workflow_records_readable(temp_db):
    """19. Test that legacy workflow records created without stored policy return policy: None gracefully."""
    repo = SQLiteWorkflowRepository(temp_db)
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("legacy-agent", "Legacy", "Tech")

    # Manually insert legacy workflow record into DB without policy column populated (or default '{}')
    conn = repo.get_connection if hasattr(repo, "get_connection") else None
    from app.db.database import get_connection
    conn = get_connection(temp_db)
    with conn:
        conn.execute(
            """
            INSERT INTO workflows (
                workflow_id, agent_id, status, started_at, completed_at,
                is_successful, halted_at_stage, rationale, selected_topic_ids,
                research_ids, draft_ids, publication_ids, traceability, policy
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("wf-legacy-001", agent.agent_id, "SUCCESS", "2026-08-09T00:00:00Z", "2026-08-09T00:01:00Z", 1, None, "Legacy run", "[]", "[]", "[]", "[]", "{}", "{}")
        )
    conn.close()

    legacy_wf = repo.get_workflow("wf-legacy-001")
    assert legacy_wf is not None
    assert legacy_wf.policy is None
