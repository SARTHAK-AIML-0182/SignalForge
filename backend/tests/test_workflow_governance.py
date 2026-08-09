from unittest.mock import MagicMock, patch
import pytest

from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
)
from app.services.publishing import BasePublishingAdapter, DryRunPublishingAdapter
from app.services.workflow import (
    WorkflowGovernanceDecision,
    WorkflowPolicy,
    evaluate_workflow_governance,
    run_agent_workflow,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_governance.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent and topic in temporary DB."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    agent = agent_repo.save_agent("agent-gov-test", "NOVA", "AI & Emerging Tech")
    topic = topic_repo.create_topic("top-gov-001", agent.agent_id, "AI Safety Governance", "Desc", "https://example.com/gov", "Tech")
    return agent, topic, temp_db


def test_valid_dry_run_governance_approval():
    """1. Test valid dry-run governance approval."""
    pol = WorkflowPolicy(max_topics=5, publication_mode="dry_run", enable_dry_run_publication=True)
    dec = evaluate_workflow_governance(pol)
    assert dec.allowed is True
    assert dec.execution_mode == "dry_run"
    assert dec.publication_allowed is True
    assert "approved" in dec.reason.lower()
    assert dec.blocked_rules == []


def test_valid_disabled_publication_governance_approval():
    """2. Test valid disabled-publication governance approval."""
    pol = WorkflowPolicy(publication_mode="disabled", enable_dry_run_publication=False)
    dec = evaluate_workflow_governance(pol)
    assert dec.allowed is True
    assert dec.execution_mode == "disabled"
    assert dec.publication_allowed is False
    assert "approved" in dec.reason.lower()
    assert dec.blocked_rules == []


def test_invalid_max_topics_rejection():
    """3. Test invalid max_topics rejection (< 1 or > 10)."""
    pol_zero = WorkflowPolicy(max_topics=0)
    dec_zero = evaluate_workflow_governance(pol_zero)
    assert dec_zero.allowed is False
    assert dec_zero.execution_mode == "blocked"
    assert len(dec_zero.blocked_rules) >= 1

    pol_over = WorkflowPolicy(max_topics=15)
    dec_over = evaluate_workflow_governance(pol_over)
    assert dec_over.allowed is False
    assert dec_over.execution_mode == "blocked"


def test_invalid_editorial_threshold_rejection():
    """4. Test invalid editorial_threshold rejection (< 0.0 or > 10.0)."""
    pol_neg = WorkflowPolicy(editorial_threshold=-1.0)
    dec_neg = evaluate_workflow_governance(pol_neg)
    assert dec_neg.allowed is False
    assert dec_neg.execution_mode == "blocked"

    pol_high = WorkflowPolicy(editorial_threshold=12.0)
    dec_high = evaluate_workflow_governance(pol_high)
    assert dec_high.allowed is False
    assert dec_high.execution_mode == "blocked"


def test_live_publication_rejection():
    """5. Test live publication rejection."""
    pol = WorkflowPolicy(publication_mode="live")
    dec = evaluate_workflow_governance(pol)
    assert dec.allowed is False
    assert dec.execution_mode == "blocked"
    assert dec.publication_allowed is False
    assert any("RULE 5" in r for r in dec.blocked_rules)


def test_social_publication_rejection():
    """6. Test social publication rejection."""
    pol = WorkflowPolicy(publication_mode="social")
    dec = evaluate_workflow_governance(pol)
    assert dec.allowed is False
    assert dec.execution_mode == "blocked"
    assert any("RULE 5" in r for r in dec.blocked_rules)


def test_arbitrary_external_adapter_rejection():
    """7. Test arbitrary external publishing adapter rejection."""
    class LiveUntrustedAdapter(BasePublishingAdapter):
        @property
        def platform_name(self) -> str:
            return "live_untrusted"

        def publish(self, draft, metadata=None):
            return {"status": "published"}

    pol = WorkflowPolicy()
    dec = evaluate_workflow_governance(pol, publishing_adapter=LiveUntrustedAdapter())
    assert dec.allowed is False
    assert dec.execution_mode == "blocked"
    assert any("RULE 7" in r for r in dec.blocked_rules)


def test_credential_injection_rejection():
    """8. Test credential/token injection rejection."""
    pol = WorkflowPolicy()
    dec = evaluate_workflow_governance(pol, extra_kwargs={"oauth_token": "secret_abc123"})
    assert dec.allowed is False
    assert dec.execution_mode == "blocked"
    assert any("RULE 6" in r for r in dec.blocked_rules)


def test_deterministic_governance_decisions():
    """9. Test that evaluation produces deterministic output across identical inputs."""
    pol = WorkflowPolicy(max_topics=4, editorial_threshold=0.8, publication_mode="dry_run")
    dec1 = evaluate_workflow_governance(pol)
    dec2 = evaluate_workflow_governance(pol)
    assert dec1.to_dict() == dec2.to_dict()


def test_governance_rejection_prevents_workflow_and_creates_zero_running_records(setup_agent):
    """10-11. Test that governance rejection prevents execution and creates ZERO SQLite records."""
    agent, topic, db_path = setup_agent
    repo = SQLiteWorkflowRepository(db_path)

    invalid_pol = WorkflowPolicy(publication_mode="live")

    with pytest.raises(ValueError, match="publication_mode|governance"):
        run_agent_workflow(agent.agent_id, config=invalid_pol, workflow_repo=repo)

    # Confirm 0 records were created
    workflows = repo.list_workflows_by_agent(agent.agent_id)
    assert len(workflows) == 0


def test_successful_governance_persisted_and_survives_reinstantiation(setup_agent):
    """12-13. Test that successful governance decision is persisted and survives repository re-instantiation."""
    agent, topic, db_path = setup_agent
    repo1 = SQLiteWorkflowRepository(db_path)

    pol = WorkflowPolicy(max_topics=3, publication_mode="dry_run")
    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        res = run_agent_workflow(agent.agent_id, config=pol, workflow_repo=repo1)

    assert res.governance is not None
    assert res.governance["allowed"] is True
    assert res.governance["execution_mode"] == "dry_run"
    assert res.governance["publication_allowed"] is True

    repo2 = SQLiteWorkflowRepository(db_path)
    fetched = repo2.get_workflow(res.workflow_id)
    assert fetched is not None
    assert fetched.governance is not None
    assert fetched.governance["allowed"] is True
    assert fetched.governance["execution_mode"] == "dry_run"


def test_governance_decision_serialization_and_deserialization():
    """Test WorkflowGovernanceDecision to_dict and from_dict methods."""
    dec = WorkflowGovernanceDecision(
        allowed=True,
        execution_mode="dry_run",
        publication_allowed=True,
        reason="Approved",
        blocked_rules=[],
        warnings=["Warn"],
        policy={"max_topics": 5},
    )
    d = dec.to_dict()
    reconstructed = WorkflowGovernanceDecision.from_dict(d)
    assert reconstructed.allowed is True
    assert reconstructed.execution_mode == "dry_run"
    assert reconstructed.warnings == ["Warn"]
