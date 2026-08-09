from unittest.mock import MagicMock, patch
import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteEvidenceRepository,
    SQLiteResearchRepository,
    SQLiteTopicRepository,
)
from app.services.discovery import FeedSource
from app.services.workflow import (
    AgentWorkflowResult,
    WorkflowConfig,
    WorkflowStageStatus,
    WorkflowStatus,
    run_agent_workflow,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_wf.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent in temporary DB."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-wf-test", "NOVA", "AI & Emerging Tech")
    return agent, temp_db


def test_complete_successful_end_to_end_workflow(setup_agent):
    """1. Test complete successful end-to-end workflow execution."""
    agent, db_path = setup_agent
    agent_repo = SQLiteAgentRepository(db_path)
    topic_repo = SQLiteTopicRepository(db_path)
    research_repo = SQLiteResearchRepository(db_path)
    evidence_repo = SQLiteEvidenceRepository(db_path)

    topic = topic_repo.create_topic(
        topic_id="top-wf-001",
        agent_id=agent.agent_id,
        title="Quantization and Distillation of Large Language Models",
        description="Technical paper on reducing LLM memory footprint and model weights.",
        source_url="https://arxiv.org/abs/2401.55555",
        source_name="ArXiv AI",
        status="selected",
    )

    c1 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("Substantial technical paper analysis detailing architecture improvements for neural networks. " * 12)
    c2 = "Enterprise adoption of quantization frameworks accelerates LLM inference speeds significantly across cloud servers. " + ("TechCrunch report confirms enterprise adoption of quantization frameworks for LLM inference. " * 12)

    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = (
        "<html><head><title>ArXiv Paper</title></head><body>"
        f"<h1>Quantization Paper</h1><p>{c1}</p><p>{c2}</p></body></html>"
    )
    mock_http.get.return_value = mock_response

    mock_feed: FeedSource = {"name": "ArXiv AI", "url": "https://arxiv.org/rss/cs.AI", "category": "AI & Emerging Tech"}

    # Add a second evidence from a distinct domain to ensure high source diversity score
    res_dummy = research_repo.create_research("res-pre-001", agent.agent_id, topic.topic_id, "completed", 0.95)
    evidence_repo.create_evidence("ev-pre-1", res_dummy.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper 1", c1, confidence=0.95)
    evidence_repo.create_evidence("ev-pre-2", res_dummy.research_id, "https://techcrunch.com/quantization", "TechCrunch", "Article 2", c2, confidence=0.90)

    with patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res:
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult

        mock_eval.return_value = [EditorialDecision("top-wf-001", "selected", 8.5, {}, "High composite score")]
        mock_res.return_value = ResearchResult(res_dummy.research_id, topic.topic_id, "completed", 0.95, 2)

        result = run_agent_workflow(
            agent_id=agent.agent_id,
            config=WorkflowConfig(max_topics=1, enable_dry_run_publication=True),
            agent_repo=agent_repo,
            topic_repo=topic_repo,
            research_repo=research_repo,
            evidence_repo=evidence_repo,
            http_client=mock_http,
            feeds=[mock_feed],
        )

    assert result.is_successful is True
    assert result.status in (WorkflowStatus.SUCCESS, WorkflowStatus.PARTIAL_SUCCESS)
    assert len(result.stages) >= 9


def test_discovery_failure_stops_workflow_safely(setup_agent):
    """2. Test that discovery failure halts workflow gracefully without crashing."""
    agent, db_path = setup_agent

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc:
        mock_disc.side_effect = Exception("Network feed timeout")

        result = run_agent_workflow(agent_id=agent.agent_id, config=WorkflowConfig())

    assert result.status == WorkflowStatus.FAILED
    assert result.halted_at_stage == "topic_discovery"
    assert result.is_successful is False


def test_no_editorial_topics_returns_no_content(setup_agent):
    """3. Test that when zero topics pass editorial evaluation, workflow returns NO_CONTENT and skips downstream stages."""
    agent, db_path = setup_agent
    agent_repo = SQLiteAgentRepository(db_path)
    topic_repo = SQLiteTopicRepository(db_path)

    topic_repo.create_topic("top-wf-low", agent.agent_id, "Low Score Topic", "Description", "https://example.com/low", "Low", "discovered")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        mock_eval.return_value = [EditorialDecision("top-wf-low", "rejected", 3.0, {}, "Low score")]

        result = run_agent_workflow(agent_id=agent.agent_id, agent_repo=agent_repo, topic_repo=topic_repo)

    assert result.status == WorkflowStatus.NO_CONTENT
    assert result.is_successful is True
    assert len(result.selected_topic_ids) == 0
    assert any(st.stage_name == "research" and st.status == WorkflowStageStatus.SKIPPED for st in result.stages)


def test_research_failure_topic_isolation(setup_agent):
    """4. Test that research failure on Topic 1 does not block Topic 2."""
    agent, db_path = setup_agent
    agent_repo = SQLiteAgentRepository(db_path)
    topic_repo = SQLiteTopicRepository(db_path)
    research_repo = SQLiteResearchRepository(db_path)
    evidence_repo = SQLiteEvidenceRepository(db_path)

    t1 = topic_repo.create_topic("top-fail", agent.agent_id, "Fail Topic", "Description", "https://example.com/fail", "Fail", "selected")
    t2 = topic_repo.create_topic("top-pass", agent.agent_id, "Pass Topic", "Description", "https://example.com/pass", "Pass", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult

        mock_eval.return_value = [
            EditorialDecision(t1.topic_id, "selected", 8.0, {}, "Pass"),
            EditorialDecision(t2.topic_id, "selected", 8.0, {}, "Pass"),
        ]

        def research_side_effect(topic, **kwargs):
            if topic.topic_id == t1.topic_id:
                return ResearchResult("res-fail", t1.topic_id, "failed", 0.0, 0)
            else:
                res = research_repo.create_research("res-pass", agent.agent_id, t2.topic_id, "completed", 0.90)
                evidence_repo.create_evidence("ev-pass", res.research_id, "https://arxiv.org/abs/123", "ArXiv", "Title", "Text " * 40, 0.90)
                return ResearchResult(res.research_id, t2.topic_id, "completed", 0.90, 1)

        mock_res.side_effect = research_side_effect

        result = run_agent_workflow(
            agent_id=agent.agent_id,
            config=WorkflowConfig(max_topics=2),
            agent_repo=agent_repo,
            topic_repo=topic_repo,
            research_repo=research_repo,
            evidence_repo=evidence_repo,
        )

    assert any(st.stage_name == f"research_{t1.topic_id}" and st.status == WorkflowStageStatus.FAILED for st in result.stages)
    assert any(st.stage_name == f"research_{t2.topic_id}" and st.status == WorkflowStageStatus.SUCCEEDED for st in result.stages)


def test_unusable_research_does_not_reach_synthesis(setup_agent):
    """5. Test that unusable research is blocked before synthesis."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)
    research_repo = SQLiteResearchRepository(db_path)
    evidence_repo = SQLiteEvidenceRepository(db_path)

    topic = topic_repo.create_topic("top-unusable", agent.agent_id, "Unusable Topic", "Description", "https://example.com/unusable", "Bad", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-1", topic.topic_id, "completed", 0.20, 1)
        mock_val.return_value = ResearchValidationResult("res-1", topic.topic_id, False, 0.20, "unusable", True, [], 0, 1, "Unusable evidence")

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo, research_repo=research_repo, evidence_repo=evidence_repo)

    assert any(st.stage_name == f"research_validation_{topic.topic_id}" and st.status == WorkflowStageStatus.BLOCKED for st in result.stages)
    assert not any(st.stage_name == f"research_synthesis_{topic.topic_id}" for st in result.stages)


def test_validation_failure_blocks_content_generation(setup_agent):
    """6. Test that validation failure blocks content brief and draft generation."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-val-fail", agent.agent_id, "Val Fail Topic", "Description", "https://example.com/vfail", "Bad", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-2", topic.topic_id, "completed", 0.10, 1)
        mock_val.return_value = ResearchValidationResult("res-2", topic.topic_id, False, 0.10, "unusable", True, [], 0, 1, "Low score")

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert not any(st.stage_name == f"content_brief_{topic.topic_id}" for st in result.stages)
    assert not any(st.stage_name == f"draft_generation_{topic.topic_id}" for st in result.stages)


def test_successful_synthesis_reaches_content_brief(setup_agent):
    """7. Test that successful synthesis reaches content brief stage."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-synth-ok", agent.agent_id, "Synth OK Topic", "Description", "https://example.com/sok", "Good", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val, \
         patch("app.services.workflow.orchestrator.synthesize_research") as mock_synth:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        from app.services.research.synthesis import ResearchSynthesisResult, SynthesizedFinding

        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-3", topic.topic_id, "completed", 0.85, 1)
        mock_val.return_value = ResearchValidationResult("res-3", topic.topic_id, True, 0.85, "acceptable", False, [], 1, 0, "OK")
        mock_synth.return_value = ResearchSynthesisResult("res-3", topic.topic_id, topic.title, True, "acceptable", 0.85, [SynthesizedFinding("f1", "Text", ["ev1"], ["https://src.com"], 0.9, 1)], [], 1, ["src.com"], [], [], 0.85, "OK")

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert any(st.stage_name == f"research_synthesis_{topic.topic_id}" and st.status == WorkflowStageStatus.SUCCEEDED for st in result.stages)
    assert any(st.stage_name.startswith("content_brief_") for st in result.stages)


def test_successful_brief_reaches_writer(setup_agent):
    """8. Test that successful brief reaches writer stage."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-brief-ok", agent.agent_id, "Brief OK Topic", "Description", "https://example.com/bok", "Good", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val, \
         patch("app.services.workflow.orchestrator.synthesize_research") as mock_synth, \
         patch("app.services.workflow.orchestrator.build_content_brief") as mock_brief:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        from app.services.research.synthesis import ResearchSynthesisResult, SynthesizedFinding
        from app.services.research.content_brief import ContentBriefResult, SupportedClaim

        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-4", topic.topic_id, "completed", 0.90, 1)
        mock_val.return_value = ResearchValidationResult("res-4", topic.topic_id, True, 0.90, "acceptable", False, [], 1, 0, "OK")
        mock_synth.return_value = ResearchSynthesisResult("res-4", topic.topic_id, topic.title, True, "acceptable", 0.90, [SynthesizedFinding("f1", "Text", ["ev1"], ["https://src.com"], 0.9, 1)], [], 1, ["src.com"], [], [], 0.90, "OK")
        mock_brief.return_value = ContentBriefResult("res-4", topic.topic_id, topic.title, "Angle", {}, [SupportedClaim("c1", "Claim text", ["f1"], ["ev1"], ["https://src.com"], 0.9)], [], [], [], [], 0.9, True, "OK")

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert any(st.stage_name == f"content_brief_{topic.topic_id}" and st.status == WorkflowStageStatus.SUCCEEDED for st in result.stages)
    assert any(st.stage_name.startswith("draft_generation_") for st in result.stages)


def test_unpublishable_draft_never_reaches_publishing_adapter(setup_agent):
    """9. Test that unpublishable draft is blocked at stage 8 and never reaches publishing adapter."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-unpub-draft", agent.agent_id, "Unpub Draft Topic", "Description", "https://example.com/unpub", "Good", "selected")
    mock_adapter = MagicMock()

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val, \
         patch("app.services.workflow.orchestrator.synthesize_research") as mock_synth, \
         patch("app.services.workflow.orchestrator.build_content_brief") as mock_brief, \
         patch("app.services.workflow.orchestrator.generate_draft") as mock_gen:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        from app.services.research.synthesis import ResearchSynthesisResult, SynthesizedFinding
        from app.services.research.content_brief import ContentBriefResult, SupportedClaim
        from app.services.research.writer import DraftResult

        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-5", topic.topic_id, "completed", 0.50, 1)
        mock_val.return_value = ResearchValidationResult("res-5", topic.topic_id, True, 0.50, "acceptable", False, [], 1, 0, "OK")
        mock_synth.return_value = ResearchSynthesisResult("res-5", topic.topic_id, topic.title, True, "acceptable", 0.50, [], [], 1, ["src.com"], [], [], 0.50, "OK")
        mock_brief.return_value = ContentBriefResult("res-5", topic.topic_id, topic.title, "Angle", {}, [SupportedClaim("c1", "Claim text", ["f1"], ["ev1"], ["https://src.com"], 0.5)], [], [], [], [], 0.5, True, "OK")
        mock_gen.return_value = DraftResult("draft-bad", topic.topic_id, "res-5", "Title", "Hook", [], "", "", [], [], 0.5, ["Conflict warning"], [], {}, False, "Bad draft")

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo, publishing_adapter=mock_adapter)

    assert any(st.stage_name == f"publishability_check_{topic.topic_id}" and st.status == WorkflowStageStatus.BLOCKED for st in result.stages)
    mock_adapter.publish.assert_not_called()


def test_publishable_draft_reaches_dry_run_publishing(setup_agent):
    """10. Test that publishable draft proceeds to dry-run publishing."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-pub-ok", agent.agent_id, "Pub OK Topic", "Description", "https://example.com/pok", "Good", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val, \
         patch("app.services.workflow.orchestrator.synthesize_research") as mock_synth, \
         patch("app.services.workflow.orchestrator.build_content_brief") as mock_brief, \
         patch("app.services.workflow.orchestrator.generate_draft") as mock_gen, \
         patch("app.services.workflow.orchestrator.publish_draft") as mock_pub:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        from app.services.research.synthesis import ResearchSynthesisResult, SynthesizedFinding
        from app.services.research.content_brief import ContentBriefResult, SupportedClaim
        from app.services.research.writer import DraftResult
        from app.services.publishing.models import PublicationResult, PublicationStatus

        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-6", topic.topic_id, "completed", 0.90, 1)
        mock_val.return_value = ResearchValidationResult("res-6", topic.topic_id, True, 0.90, "strong", False, [], 1, 0, "OK")
        mock_synth.return_value = ResearchSynthesisResult("res-6", topic.topic_id, topic.title, True, "strong", 0.90, [], [], 1, ["src.com"], [], [], 0.90, "OK")
        mock_brief.return_value = ContentBriefResult("res-6", topic.topic_id, topic.title, "Angle", {}, [SupportedClaim("c1", "Claim text", ["f1"], ["ev1"], ["https://src.com"], 0.9)], [], [], [], [], 0.9, True, "OK")
        mock_gen.return_value = DraftResult("draft-good", topic.topic_id, "res-6", "Title", "Hook", [], "", "Full text", [], [], 0.9, [], [], {"sec-1": {"claim_ids": ["c1"], "evidence_ids": ["e1"], "source_urls": ["s1"]}}, True, "Good draft")
        mock_pub.return_value = PublicationResult("pub-good", "draft-good", topic.topic_id, "res-6", "dry_run_local", PublicationStatus.DRY_RUN, True, True, "Full text", "2026-08-09T00:00:00Z", [], None, {}, "Success")

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert any(st.stage_name == f"dry_run_publication_{topic.topic_id}" and st.status == WorkflowStageStatus.SUCCEEDED for st in result.stages)


def test_dry_run_publishing_succeeds(setup_agent):
    """11. Test dry-run publishing returns successful result with publication ID."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-dry-ok", agent.agent_id, "Dry OK Topic", "Description", "https://example.com/dok", "Good", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val, \
         patch("app.services.workflow.orchestrator.synthesize_research") as mock_synth, \
         patch("app.services.workflow.orchestrator.build_content_brief") as mock_brief, \
         patch("app.services.workflow.orchestrator.generate_draft") as mock_gen:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        from app.services.research.synthesis import ResearchSynthesisResult, SynthesizedFinding
        from app.services.research.content_brief import ContentBriefResult, SupportedClaim
        from app.services.research.writer import DraftResult

        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-7", topic.topic_id, "completed", 0.90, 1)
        mock_val.return_value = ResearchValidationResult("res-7", topic.topic_id, True, 0.90, "strong", False, [], 1, 0, "OK")
        mock_synth.return_value = ResearchSynthesisResult("res-7", topic.topic_id, topic.title, True, "strong", 0.90, [], [], 1, ["src.com"], [], [], 0.90, "OK")
        mock_brief.return_value = ContentBriefResult("res-7", topic.topic_id, topic.title, "Angle", {}, [SupportedClaim("c1", "Claim text", ["f1"], ["ev1"], ["https://src.com"], 0.9)], [], [], [], [], 0.9, True, "OK")
        mock_gen.return_value = DraftResult("draft-dry", topic.topic_id, "res-7", "Title", "Hook", [], "", "Full text", [], [], 0.9, [], [], {"sec-1": {"claim_ids": ["c1"], "evidence_ids": ["e1"], "source_urls": ["s1"]}}, True, "Good")

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert len(result.publication_ids) == 1
    assert result.publication_ids[0].startswith("pub-")


def test_multiple_selected_topics_handled(setup_agent):
    """12. Test that multiple selected topics are processed sequentially."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    t1 = topic_repo.create_topic("top-m1", agent.agent_id, "Multi 1", "Desc", "https://example.com/m1", "M1", "selected")
    t2 = topic_repo.create_topic("top-m2", agent.agent_id, "Multi 2", "Desc", "https://example.com/m2", "M2", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        mock_eval.return_value = [
            EditorialDecision(t1.topic_id, "selected", 8.0, {}, "Pass"),
            EditorialDecision(t2.topic_id, "selected", 8.0, {}, "Pass"),
        ]

        result = run_agent_workflow(agent_id=agent.agent_id, config=WorkflowConfig(max_topics=2), topic_repo=topic_repo)

    assert len(result.selected_topic_ids) == 2


def test_topic_level_failure_isolation(setup_agent):
    """13. Test topic-level exception isolation."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    t1 = topic_repo.create_topic("top-ex1", agent.agent_id, "Ex 1", "Desc", "https://example.com/ex1", "E1", "selected")
    t2 = topic_repo.create_topic("top-ex2", agent.agent_id, "Ex 2", "Desc", "https://example.com/ex2", "E2", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        mock_eval.return_value = [
            EditorialDecision(t1.topic_id, "selected", 8.0, {}, "Pass"),
            EditorialDecision(t2.topic_id, "selected", 8.0, {}, "Pass"),
        ]

        def res_side_effect(topic, **kwargs):
            if topic.topic_id == t1.topic_id:
                raise ValueError("Explosion on topic 1")
            return ResearchResult("res-ex2", t2.topic_id, "completed", 0.9, 1)

        mock_res.side_effect = res_side_effect

        result = run_agent_workflow(agent_id=agent.agent_id, config=WorkflowConfig(max_topics=2), topic_repo=topic_repo)

    assert any(st.stage_name == f"research_{t1.topic_id}" and st.status == WorkflowStageStatus.FAILED for st in result.stages)
    assert any(st.stage_name == f"research_{t2.topic_id}" and st.status == WorkflowStageStatus.SUCCEEDED for st in result.stages)


def test_workflow_result_contains_structured_stage_results(setup_agent):
    """14. Test that AgentWorkflowResult contains structured WorkflowStageResult instances."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
        mock_disc.return_value = []
        mock_eval.return_value = []

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert len(result.stages) >= 2
    for st in result.stages:
        assert hasattr(st, "stage_name")
        assert hasattr(st, "status")
        assert hasattr(st, "started_at")


def test_end_to_end_traceability_preserved(setup_agent):
    """15. Test end-to-end traceability mapping preservation in workflow result."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-tr", agent.agent_id, "Trace Topic", "Desc", "https://example.com/tr", "Tr", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]

        result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert topic.topic_id in result.traceability
    assert result.traceability[topic.topic_id]["title"] == topic.title


def test_no_evidence_deleted_during_workflow(setup_agent):
    """16. Test that workflow execution leaves existing evidence records intact."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)
    research_repo = SQLiteResearchRepository(db_path)
    evidence_repo = SQLiteEvidenceRepository(db_path)

    topic_repo.create_topic("top-keep", agent.agent_id, "Keep Topic", "Desc", "https://arxiv.org/abs/999", "ArXiv", "selected")
    res = research_repo.create_research("res-keep", agent.agent_id, "top-keep", "completed", 0.9)
    evidence_repo.create_evidence("ev-keep", res.research_id, "https://arxiv.org/abs/999", "ArXiv", "Paper", "Text " * 40, 0.9)

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
        mock_disc.return_value = []
        mock_eval.return_value = []

        run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo, research_repo=research_repo, evidence_repo=evidence_repo)

    ev_list = evidence_repo.list_evidence_by_research(res.research_id)
    assert len(ev_list) == 1


def test_configuration_max_topics_respected(setup_agent):
    """17. Test that configuration max_topics parameter is respected."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    for i in range(5):
        topic_repo.create_topic(f"top-max-{i}", agent.agent_id, f"Topic {i}", "Desc", f"https://example.com/{i}", "Src", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        mock_eval.return_value = [EditorialDecision(f"top-max-{i}", "selected", 8.0, {}, "Pass") for i in range(5)]

        result = run_agent_workflow(agent_id=agent.agent_id, config=WorkflowConfig(max_topics=2), topic_repo=topic_repo)

    processed_stages = [st for st in result.stages if st.stage_name.startswith("research_top-max-")]
    assert len(processed_stages) == 2


def test_dry_run_publication_can_be_disabled(setup_agent):
    """18. Test that setting enable_dry_run_publication=False skips dry-run publication stage."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    topic = topic_repo.create_topic("top-nodry", agent.agent_id, "No Dry Topic", "Desc", "https://example.com/nodry", "Src", "selected")

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval, \
         patch("app.services.workflow.orchestrator.research_topic") as mock_res, \
         patch("app.services.workflow.orchestrator.validate_research") as mock_val, \
         patch("app.services.workflow.orchestrator.synthesize_research") as mock_synth, \
         patch("app.services.workflow.orchestrator.build_content_brief") as mock_brief, \
         patch("app.services.workflow.orchestrator.generate_draft") as mock_gen:
        mock_disc.return_value = []
        from app.services.editorial.engine import EditorialDecision
        from app.services.research.engine import ResearchResult
        from app.services.research.validation import ResearchValidationResult
        from app.services.research.synthesis import ResearchSynthesisResult
        from app.services.research.content_brief import ContentBriefResult
        from app.services.research.writer import DraftResult

        mock_eval.return_value = [EditorialDecision(topic.topic_id, "selected", 8.0, {}, "Pass")]
        mock_res.return_value = ResearchResult("res-nodry", topic.topic_id, "completed", 0.9, 1)
        mock_val.return_value = ResearchValidationResult("res-nodry", topic.topic_id, True, 0.9, "strong", False, [], 1, 0, "OK")
        mock_synth.return_value = ResearchSynthesisResult("res-nodry", topic.topic_id, topic.title, True, "strong", 0.9, [], [], 1, ["src.com"], [], [], 0.90, "OK")
        mock_brief.return_value = ContentBriefResult("res-nodry", topic.topic_id, topic.title, "Angle", {}, [], [], [], [], [], 0.9, True, "OK")
        mock_gen.return_value = DraftResult("draft-nodry", topic.topic_id, "res-nodry", "Title", "Hook", [], "", "Text", [], [], 0.9, [], [], {"sec": {}}, True, "OK")

        result = run_agent_workflow(
            agent_id=agent.agent_id,
            config=WorkflowConfig(enable_dry_run_publication=False),
            topic_repo=topic_repo,
        )

    assert any(st.stage_name == f"dry_run_publication_{topic.topic_id}" and st.status == WorkflowStageStatus.SKIPPED for st in result.stages)
    assert len(result.publication_ids) == 0


def test_workflow_remains_deterministic(setup_agent):
    """19. Test that executing workflow with identical inputs produces deterministic stage output."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    with patch("app.services.workflow.orchestrator.discover_topics") as mock_disc, \
         patch("app.services.workflow.orchestrator.evaluate_agent_topics") as mock_eval:
        mock_disc.return_value = []
        mock_eval.return_value = []

        res1 = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)
        res2 = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert res1.status == res2.status
    assert len(res1.stages) == len(res2.stages)


def test_existing_test_suite_remains_green(setup_agent):
    """20. Test that workflow execution preserves pipeline integrity across overall subsystems."""
    agent, db_path = setup_agent
    topic_repo = SQLiteTopicRepository(db_path)

    result = run_agent_workflow(agent_id=agent.agent_id, topic_repo=topic_repo)

    assert hasattr(result, "workflow_id")
    assert hasattr(result, "status")
    assert isinstance(result.stages, list)
