from unittest.mock import patch
import pytest

from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLitePersonaRepository,
    SQLitePostRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
)
from app.services.editorial import EditorialDecision
from app.services.research.content_brief import ContentBriefResult, SupportedClaim
from app.services.research.synthesis import ResearchSynthesisResult, SynthesizedFinding
from app.services.research.validation import ResearchValidationResult
from app.services.research.writer import DraftResult, DraftSection
from app.services.workflow import WorkflowPolicy, run_agent_workflow
from app.services.workflow.diagnostics import sanitize_failure_reason


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_failure_adv.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_multi_topics(temp_db):
    """Fixture setting up agent with 3 topics for multi-topic failure tests."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)
    post_repo = SQLitePostRepository(temp_db)
    persona_repo = SQLitePersonaRepository(temp_db)

    agent = agent_repo.save_agent("agent-fail-adv", "NOVA", "AI & Tech")
    topics = [
        topic_repo.create_topic(
            f"top-fail-{i:03d}",
            agent.agent_id,
            f"Topic Title {i:03d} for Autonomous AI Research",
            f"Description for topic {i:03d}",
            f"https://example.com/topic-{i}",
            "Tech Daily"
        )
        for i in range(1, 4)
    ]
    return agent, topics, temp_db, agent_repo, topic_repo, wf_repo, post_repo, persona_repo


def mock_successful_draft(brief):
    sec = DraftSection(section_id="sec1", heading="Heading", content="Content text", claim_ids=["c1"], evidence_ids=["e1"], source_urls=["https://example.com"])
    return DraftResult(
        draft_id=f"draft-{brief.research_id}",
        topic_id=brief.topic_id,
        research_id=brief.research_id,
        title="Title",
        hook="Hook",
        sections=[sec],
        conclusion="Conclusion",
        full_text="Full text content",
        supported_claims_used=[],
        source_references=[],
        confidence=0.9,
        warnings=[],
        limitations=[],
        traceability={"sections": ["sec1"], "claims": ["c1"]},
        is_publishable=True,
        rationale="Good draft",
    )


def mock_usable_validation(research_id, **kwargs):
    top_id = research_id.replace("res-", "")
    return ResearchValidationResult(research_id=research_id, topic_id=top_id, is_usable=True, overall_score=0.9, quality_classification="strong", needs_additional_research=False, evidence_items=[], usable_evidence_count=2, rejected_evidence_count=0, rationale="High quality")


def mock_usable_synthesis(research_id, **kwargs):
    top_id = research_id.replace("res-", "")
    return ResearchSynthesisResult(research_id=research_id, topic_id=top_id, topic_title="Title", is_usable=True, quality_classification="strong", overall_score=0.9, findings=[SynthesizedFinding(finding_id="f1", text="Finding text", evidence_ids=["e1"], source_urls=["https://example.com"], confidence=0.9, support_count=1)], source_references=[], source_diversity_count=1, distinct_domains=["example.com"], detected_conflicts=[], limitations=[], confidence=0.9, rationale="High quality")


def mock_usable_brief(research_id, **kwargs):
    top_id = research_id.replace("res-", "")
    return ContentBriefResult(research_id=research_id, topic_id=top_id, topic_title="Title", angle="Technical Analysis", audience={"tone": "authoritative"}, claims=[SupportedClaim(claim_id="c1", claim_text="Claim", finding_ids=["f1"], evidence_ids=["e1"], source_urls=["https://example.com"], confidence=0.9)], findings=[], sources=[], limitations=[], constraints=[], confidence=0.9, is_usable=True, rationale="Good brief")


def make_editorial_decisions(topics_list):
    return [
        EditorialDecision(topic_id=t.topic_id, decision="selected", total_score=8.5, factors={}, rationale="High score")
        for t in topics_list
    ]


def test_scenario_a_topic1_fails_research_topic2_succeeds(setup_multi_topics):
    """Scenario A: Topic 1 fails research, Topic 2 succeeds through dry-run publication."""
    agent, topics, _, _, topic_repo, wf_repo, post_repo, persona_repo = setup_multi_topics
    target_topics = topics[:2]

    def mock_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        if topic.topic_id == target_topics[0].topic_id:
            return ResearchResult(research_id="r-fail", topic_id=topic.topic_id, status="failed", confidence=0.0, evidence_count=0)
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=target_topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(target_topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_usable_validation):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_usable_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_successful_draft):
                                result = run_agent_workflow(
                                    agent_id=agent.agent_id,
                                    config=WorkflowPolicy(max_topics=2, editorial_threshold=0.5),
                                    topic_repo=topic_repo,
                                    workflow_repo=wf_repo,
                                    post_repo=post_repo,
                                    persona_repo=persona_repo,
                                )

    assert result.status == "PARTIAL_SUCCESS"
    assert result.is_successful is True

    # Check stage results
    t1_stages = [s for s in result.stages if target_topics[0].topic_id in s.stage_name]
    assert len(t1_stages) == 1
    assert t1_stages[0].status == "FAILED"

    t2_stages = [s for s in result.stages if target_topics[1].topic_id in s.stage_name]
    assert len(t2_stages) >= 6
    assert t2_stages[-1].status == "SUCCEEDED"

    # Check diagnostics
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag["topic_id"] == target_topics[0].topic_id
    assert "research" in diag["failed_stage"]


def test_scenario_b_topic1_succeeds_topic2_fails_writing_topic3_succeeds(setup_multi_topics):
    """Scenario B: Topic 1 succeeds, Topic 2 fails during draft generation (writing), Topic 3 succeeds."""
    agent, topics, _, _, topic_repo, wf_repo, post_repo, persona_repo = setup_multi_topics

    def mock_success_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    def mock_generate_draft(brief):
        if brief.topic_id == topics[1].topic_id:
            raise ValueError("Writing engine syntax formatting error")
        return mock_successful_draft(brief)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_success_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_usable_validation):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_usable_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_generate_draft):
                                result = run_agent_workflow(
                                    agent_id=agent.agent_id,
                                    config=WorkflowPolicy(max_topics=3, editorial_threshold=0.5),
                                    topic_repo=topic_repo,
                                    workflow_repo=wf_repo,
                                    post_repo=post_repo,
                                    persona_repo=persona_repo,
                                )

    assert result.status == "PARTIAL_SUCCESS"
    assert len(result.publication_ids) == 2
    assert len(result.diagnostics) == 1

    diag = result.diagnostics[0]
    assert diag["topic_id"] == topics[1].topic_id
    assert "draft_generation" in diag["failed_stage"]
    assert "ValueError" in diag["sanitized_reason"]


def test_scenario_c_multiple_independent_topics_fail_at_different_stages(setup_multi_topics):
    """Scenario C: Multiple independent topics fail at different stages (research and brief), while Topic 3 succeeds."""
    agent, topics, _, _, topic_repo, wf_repo, post_repo, persona_repo = setup_multi_topics

    def mock_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        if topic.topic_id == topics[0].topic_id:
            raise RuntimeError("C:\\SecretDB\\Path\\sqlite3.db failed")
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    def mock_brief(research_id, **kwargs):
        if research_id == f"res-{topics[1].topic_id}":
            raise KeyError("Claim validation failure")
        return ContentBriefResult(
            research_id=research_id,
            topic_id=topics[2].topic_id,
            topic_title="Title",
            angle="Analysis",
            audience={"tone": "tech"},
            claims=[SupportedClaim(claim_id="c1", claim_text="Text", finding_ids=["f1"], evidence_ids=["e1"], source_urls=["https://example.com"], confidence=0.9)],
            findings=[],
            sources=[],
            limitations=[],
            constraints=[],
            confidence=0.9,
            is_usable=True,
            rationale="Good brief",
        )

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_usable_validation):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_successful_draft):
                                result = run_agent_workflow(
                                    agent_id=agent.agent_id,
                                    config=WorkflowPolicy(max_topics=3, editorial_threshold=0.5),
                                    topic_repo=topic_repo,
                                    workflow_repo=wf_repo,
                                    post_repo=post_repo,
                                    persona_repo=persona_repo,
                                )

    assert result.status == "PARTIAL_SUCCESS"
    assert len(result.diagnostics) == 2

    diag1 = result.diagnostics[0]
    assert "SecretDB" not in diag1["sanitized_reason"]

    diag2 = result.diagnostics[1]
    assert "content_brief" in diag2["failed_stage"]


def test_scenario_d_all_executable_topics_fail(setup_multi_topics):
    """Scenario D: All executable topics fail, resulting in overall FAILED status."""
    agent, topics, _, _, topic_repo, wf_repo, post_repo, persona_repo = setup_multi_topics
    target_topics = topics[:2]

    def mock_failed_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        return ResearchResult(research_id="r-fail", topic_id=topic.topic_id, status="failed", confidence=0.0, evidence_count=0)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=target_topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(target_topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_failed_research):
                result = run_agent_workflow(
                    agent_id=agent.agent_id,
                    config=WorkflowPolicy(max_topics=2, editorial_threshold=0.5),
                    topic_repo=topic_repo,
                    workflow_repo=wf_repo,
                    post_repo=post_repo,
                    persona_repo=persona_repo,
                )

    assert result.status == "FAILED"
    assert result.is_successful is False
    assert len(result.diagnostics) == 2


def test_scenario_e_topic_blocked_while_another_publishes(setup_multi_topics):
    """Scenario E: Topic 1 is BLOCKED (unusable research validation) while Topic 2 successfully publishes."""
    agent, topics, _, _, topic_repo, wf_repo, post_repo, persona_repo = setup_multi_topics
    target_topics = topics[:2]

    def mock_success_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    def mock_validate(research_id, **kwargs):
        if research_id == f"res-{target_topics[0].topic_id}":
            return ResearchValidationResult(research_id=research_id, topic_id=target_topics[0].topic_id, is_usable=False, overall_score=0.2, quality_classification="low", needs_additional_research=True, evidence_items=[], usable_evidence_count=0, rejected_evidence_count=2, rationale="Low quality")
        return ResearchValidationResult(research_id=research_id, topic_id=target_topics[1].topic_id, is_usable=True, overall_score=0.9, quality_classification="strong", needs_additional_research=False, evidence_items=[], usable_evidence_count=2, rejected_evidence_count=0, rationale="High quality")

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=target_topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(target_topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_success_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_validate):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_usable_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_successful_draft):
                                result = run_agent_workflow(
                                    agent_id=agent.agent_id,
                                    config=WorkflowPolicy(max_topics=2, editorial_threshold=0.5),
                                    topic_repo=topic_repo,
                                    workflow_repo=wf_repo,
                                    post_repo=post_repo,
                                    persona_repo=persona_repo,
                                )

    assert result.status == "PARTIAL_SUCCESS"
    assert len(result.publication_ids) == 1
    assert len(result.diagnostics) == 0


def test_scenario_g_process_restart_preserves_diagnostics(setup_multi_topics):
    """Scenario G: Diagnostics survive SQLite persistence and process restart (repository re-instantiation)."""
    agent, topics, temp_db, _, topic_repo, wf_repo, post_repo, persona_repo = setup_multi_topics
    target_topics = topics[:2]

    def mock_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        if topic.topic_id == target_topics[0].topic_id:
            return ResearchResult(research_id="r-fail", topic_id=topic.topic_id, status="failed", confidence=0.0, evidence_count=0)
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=target_topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(target_topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_usable_validation):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_usable_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_successful_draft):
                                res = run_agent_workflow(
                                    agent_id=agent.agent_id,
                                    config=WorkflowPolicy(max_topics=2, editorial_threshold=0.5),
                                    topic_repo=topic_repo,
                                    workflow_repo=wf_repo,
                                    post_repo=post_repo,
                                    persona_repo=persona_repo,
                                )

    new_wf_repo = SQLiteWorkflowRepository(temp_db)
    loaded_wf = new_wf_repo.get_workflow(res.workflow_id)

    assert loaded_wf is not None
    assert loaded_wf.workflow_id == res.workflow_id
    assert "diagnostics" in loaded_wf.traceability
    assert len(loaded_wf.traceability["diagnostics"]) == 1
    assert loaded_wf.traceability["diagnostics"][0]["topic_id"] == target_topics[0].topic_id


def test_sanitize_failure_reason_function():
    """Verify sanitize_failure_reason strips sensitive info."""
    raw_path_exc = Exception("Failed at C:\\Users\\hp\\secret_db.sqlite")
    sanitized = sanitize_failure_reason(raw_path_exc)
    assert "secret_db" not in sanitized
    assert "Exception" in sanitized

    raw_sql_str = "SELECT * FROM users WHERE password = '123'"
    sanitized_str = sanitize_failure_reason(raw_sql_str)
    assert "password" not in sanitized_str
    assert "halted" in sanitized_str
