from unittest.mock import patch
import pytest

from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
)
from app.services.editorial.engine import EditorialDecision
from app.services.publishing.service import PublicationResult
from app.services.research.content_brief import ContentBriefResult
from app.services.research.engine import ResearchResult
from app.services.research.synthesis import ResearchSynthesisResult
from app.services.research.validation import ResearchValidationResult
from app.services.research.writer import DraftResult
from app.services.workflow import WorkflowConfig, run_agent_workflow
from app.services.workflow.models import (
    AgentWorkflowResult,
    WorkflowStageStatus,
    WorkflowStatus,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_failure_recovery.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent and topic in temporary DB."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    agent = agent_repo.save_agent("agent-fail-test", "NOVA", "AI & Emerging Tech")
    topic = topic_repo.create_topic("top-quantum-001", agent.agent_id, "Quantum Computing Breakthroughs", "Description", "https://example.com/quantum", "Tech")
    return agent, topic, temp_db


def test_initial_running_state_persisted(setup_agent):
    """1. Test that initial RUNNING state is persisted before workflow completion."""
    agent, topic, db_path = setup_agent
    workflow_repo = SQLiteWorkflowRepository(db_path)

    # Patch discover_topics to verify persistence inside workflow repo before stage 1 finishes
    persisted_states = []

    def mock_discover(*args, **kwargs):
        # Query DB directly during discovery to verify RUNNING state was saved
        workflows = workflow_repo.list_workflows_by_agent(agent.agent_id)
        if workflows:
            persisted_states.append(workflows[0].status)
        return [topic]

    with patch("app.services.workflow.orchestrator.discover_topics", side_effect=mock_discover):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "High score")]
            run_agent_workflow(agent.agent_id, workflow_repo=workflow_repo)

    assert WorkflowStatus.RUNNING in persisted_states


def test_controlled_research_failure_becomes_failed(setup_agent):
    """2. Test that controlled research stage failure transitions workflow to FAILED."""
    agent, topic, db_path = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "Selected")]
            with patch("app.services.workflow.orchestrator.research_topic") as mock_res:
                mock_res.side_effect = RuntimeError("Network error during scraping")
                res = run_agent_workflow(agent.agent_id, workflow_repo=SQLiteWorkflowRepository(db_path))

    assert res.status == WorkflowStatus.FAILED
    assert res.is_successful is False
    assert res.completed_at != ""
    assert res.halted_at_stage == f"research_{topic.topic_id}"
    assert "FAILED" in res.rationale
    assert "RuntimeError" in res.stages[-1].rationale
    # Confirm completed stages are preserved
    stage_names = [st.stage_name for st in res.stages]
    assert "topic_discovery" in stage_names
    assert "editorial_evaluation" in stage_names
    assert f"research_{topic.topic_id}" in stage_names


def test_controlled_synthesis_failure_becomes_failed(setup_agent):
    """3. Test that synthesis stage exception transitions workflow to FAILED."""
    agent, topic, db_path = setup_agent

    dummy_res = ResearchResult(
        research_id="res-123",
        topic_id=topic.topic_id,
        status="completed",
        confidence=0.85,
        evidence_count=2,
    )
    dummy_val = ResearchValidationResult(
        research_id="res-123",
        topic_id=topic.topic_id,
        is_usable=True,
        overall_score=0.8,
        quality_classification="strong",
        needs_additional_research=False,
        evidence_items=[],
        usable_evidence_count=2,
        rejected_evidence_count=0,
        rationale="Passed validation",
    )

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "Selected")]
            with patch("app.services.workflow.orchestrator.research_topic", return_value=dummy_res):
                with patch("app.services.workflow.orchestrator.validate_research", return_value=dummy_val):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=ValueError("Synthesis invalid input")):
                        res = run_agent_workflow(agent.agent_id, workflow_repo=SQLiteWorkflowRepository(db_path))

    assert res.status == WorkflowStatus.FAILED
    assert res.is_successful is False
    assert res.halted_at_stage is not None


def test_controlled_writer_failure_becomes_failed(setup_agent):
    """4. Test that draft generation exception transitions workflow to FAILED."""
    agent, topic, db_path = setup_agent

    dummy_res = ResearchResult("res-123", topic.topic_id, "completed", 0.85, 2)
    dummy_val = ResearchValidationResult("res-123", topic.topic_id, True, 0.8, "strong", False, [], 2, 0, "Passed")
    dummy_synth = ResearchSynthesisResult("res-123", topic.topic_id, topic.title, True, "strong", 0.8, [], [], 1, ["example.com"], [], [], 0.8, "Ok")
    dummy_brief = ContentBriefResult("res-123", topic.topic_id, topic.title, "Angle", {}, [], [], [], [], [], 0.9, True, "OK")

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "Selected")]
            with patch("app.services.workflow.orchestrator.research_topic", return_value=dummy_res):
                with patch("app.services.workflow.orchestrator.validate_research", return_value=dummy_val):
                    with patch("app.services.workflow.orchestrator.synthesize_research", return_value=dummy_synth):
                        with patch("app.services.workflow.orchestrator.build_content_brief", return_value=dummy_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=KeyError("Missing section key")):
                                res = run_agent_workflow(agent.agent_id, workflow_repo=SQLiteWorkflowRepository(db_path))

    assert res.status == WorkflowStatus.FAILED
    assert res.is_successful is False


def test_controlled_publishing_failure_cannot_become_success(setup_agent):
    """5. Test that publishing simulation failure never produces a SUCCESS status."""
    agent, topic, db_path = setup_agent

    dummy_res = ResearchResult("res-123", topic.topic_id, "completed", 0.85, 2)
    dummy_val = ResearchValidationResult("res-123", topic.topic_id, True, 0.8, "strong", False, [], 2, 0, "Passed")
    dummy_synth = ResearchSynthesisResult("res-123", topic.topic_id, topic.title, True, "strong", 0.8, [], [], 1, ["example.com"], [], [], 0.8, "Ok")
    dummy_brief = ContentBriefResult("res-123", topic.topic_id, topic.title, "Angle", {}, [], [], [], [], [], 0.9, True, "OK")
    dummy_draft = DraftResult("draft-1", topic.topic_id, "res-123", "Title", "Hook", [], "Concl", "Text", [], [], 0.9, [], [], {}, True, "Ok")

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "Selected")]
            with patch("app.services.workflow.orchestrator.research_topic", return_value=dummy_res):
                with patch("app.services.workflow.orchestrator.validate_research", return_value=dummy_val):
                    with patch("app.services.workflow.orchestrator.synthesize_research", return_value=dummy_synth):
                        with patch("app.services.workflow.orchestrator.build_content_brief", return_value=dummy_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", return_value=dummy_draft):
                                with patch("app.services.workflow.orchestrator.publish_draft", side_effect=IOError("Simulated publishing adapter timeout")):
                                    res = run_agent_workflow(agent.agent_id, workflow_repo=SQLiteWorkflowRepository(db_path))

    assert res.status != WorkflowStatus.SUCCESS
    assert res.status in (WorkflowStatus.FAILED, WorkflowStatus.PARTIAL_SUCCESS, WorkflowStatus.NO_CONTENT)


def test_blocked_stage_prevents_publication(setup_agent):
    """6. Test that an unusable validation BLOCKED stage prevents downstream publication."""
    agent, topic, db_path = setup_agent

    dummy_res = ResearchResult("res-123", topic.topic_id, "completed", 0.85, 2)
    dummy_val = ResearchValidationResult("res-123", topic.topic_id, False, 0.3, "unusable", True, [], 0, 2, "Fails quality threshold")

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "Selected")]
            with patch("app.services.workflow.orchestrator.research_topic", return_value=dummy_res):
                with patch("app.services.workflow.orchestrator.validate_research", return_value=dummy_val):
                    with patch("app.services.workflow.orchestrator.publish_draft") as mock_pub:
                        res = run_agent_workflow(agent.agent_id, workflow_repo=SQLiteWorkflowRepository(db_path))
                        # Publication adapter must never be called
                        assert mock_pub.call_count == 0

    stage_statuses = {st.stage_name: st.status for st in res.stages}
    assert stage_statuses[f"research_validation_{topic.topic_id}"] == WorkflowStageStatus.BLOCKED
    assert f"dry_run_publication_{topic.topic_id}" not in stage_statuses


def test_skipped_stages_when_zero_topics_selected(setup_agent):
    """7. Test that when zero topics pass editorial selection, remaining stages are recorded as SKIPPED and workflow is NO_CONTENT."""
    agent, topic, db_path = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "rejected", 3.0, {}, "Rejected")]
            res = run_agent_workflow(agent.agent_id, workflow_repo=SQLiteWorkflowRepository(db_path))

    assert res.status == WorkflowStatus.NO_CONTENT
    assert res.is_successful is True
    assert len(res.selected_topic_ids) == 0
    skipped = [st for st in res.stages if st.status == WorkflowStageStatus.SKIPPED]
    assert len(skipped) == 7


def test_persistence_failure_returns_safe_failed_result(setup_agent):
    """8. Test that if save_workflow raises an exception during completion of a successful run, a safe FAILED result is returned."""
    agent, topic, db_path = setup_agent

    class FailingWorkflowRepo(SQLiteWorkflowRepository):
        def save_workflow(self, result: AgentWorkflowResult) -> AgentWorkflowResult:
            if result.status != WorkflowStatus.RUNNING:
                raise RuntimeError("Database disk full simulation")
            return super().save_workflow(result)

    failing_repo = FailingWorkflowRepo(db_path)
    dummy_res = ResearchResult("res-123", topic.topic_id, "completed", 0.85, 2)
    dummy_val = ResearchValidationResult("res-123", topic.topic_id, True, 0.8, "strong", False, [], 2, 0, "Passed")
    dummy_synth = ResearchSynthesisResult("res-123", topic.topic_id, topic.title, True, "strong", 0.8, [], [], 1, ["example.com"], [], [], 0.8, "Ok")
    dummy_brief = ContentBriefResult("res-123", topic.topic_id, topic.title, "Angle", {}, [], [], [], [], [], 0.9, True, "OK")
    dummy_draft = DraftResult("draft-1", topic.topic_id, "res-123", "Title", "Hook", [], "Concl", "Text", [], [], 0.9, [], [], {}, True, "Ok")
    dummy_pub = PublicationResult("pub-1", "draft-1", topic.topic_id, agent.agent_id, "dry_run", "published", True, "2026-08-09T00:00:00Z", "Ok", {})

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "Selected")]
            with patch("app.services.workflow.orchestrator.research_topic", return_value=dummy_res):
                with patch("app.services.workflow.orchestrator.validate_research", return_value=dummy_val):
                    with patch("app.services.workflow.orchestrator.synthesize_research", return_value=dummy_synth):
                        with patch("app.services.workflow.orchestrator.build_content_brief", return_value=dummy_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", return_value=dummy_draft):
                                with patch("app.services.workflow.orchestrator.publish_draft", return_value=dummy_pub):
                                    res = run_agent_workflow(agent.agent_id, workflow_repo=failing_repo)

    assert res.status == WorkflowStatus.FAILED
    assert res.is_successful is False
    assert res.halted_at_stage == "persistence"
    assert "database" not in res.rationale.lower()  # Sanitized rationale


def test_persisted_failure_state_reconstruction_after_restart(setup_agent):
    """9. Test that GETting a failed workflow from SQLite reconstructs identical failure state and traceability."""
    agent, topic, db_path = setup_agent
    workflow_repo = SQLiteWorkflowRepository(db_path)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[topic]):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
            mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.5, {}, "Selected")]
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=ValueError("Scraping timeout")):
                res_saved = run_agent_workflow(agent.agent_id, workflow_repo=workflow_repo)

    # Re-instantiate repository (simulating process restart)
    repo_restart = SQLiteWorkflowRepository(db_path)
    res_reconstructed = repo_restart.get_workflow(res_saved.workflow_id)

    assert res_reconstructed is not None
    assert res_reconstructed.workflow_id == res_saved.workflow_id
    assert res_reconstructed.status == WorkflowStatus.FAILED
    assert res_reconstructed.is_successful is False
    assert res_reconstructed.halted_at_stage == res_saved.halted_at_stage
    assert len(res_reconstructed.stages) == len(res_saved.stages)
