from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLitePersonaRepository,
    SQLitePostRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
    get_agent_repository,
    get_persona_repository,
    get_post_repository,
    get_workflow_repository,
)
from app.services.editorial import EditorialDecision
from app.services.research.content_brief import ContentBriefResult, SupportedClaim
from app.services.research.synthesis import ResearchSynthesisResult, SynthesizedFinding
from app.services.research.validation import ResearchValidationResult
from app.services.research.writer import DraftResult, DraftSection
from app.services.workflow import WorkflowPolicy, run_agent_workflow


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_diag_api.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_api_agent(temp_db):
    """Fixture setting up agent and repositories for failure diagnostics API tests."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)
    post_repo = SQLitePostRepository(temp_db)
    persona_repo = SQLitePersonaRepository(temp_db)

    agent = agent_repo.save_agent("agent-diag-api", "NOVA", "AI & Emerging Tech")
    topics = [
        topic_repo.create_topic(
            f"top-diag-{i:03d}",
            agent.agent_id,
            f"Topic Title {i:03d} for Autonomous AI Research",
            f"Description for topic {i:03d}",
            f"https://example.com/topic-{i}",
            "Tech Daily"
        )
        for i in range(1, 3)
    ]

    app.dependency_overrides[get_agent_repository] = lambda: agent_repo
    app.dependency_overrides[get_workflow_repository] = lambda: wf_repo
    app.dependency_overrides[get_post_repository] = lambda: post_repo
    app.dependency_overrides[get_persona_repository] = lambda: persona_repo

    client = TestClient(app)
    yield agent, topics, client, temp_db, agent_repo, topic_repo, wf_repo, post_repo
    app.dependency_overrides.clear()


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


def test_workflow_run_endpoint_returns_diagnostics(setup_api_agent):
    """Test POST /api/agent/{agent_id}/workflow/run exposes diagnostics for failed topics."""
    agent, topics, client, _, _, topic_repo, wf_repo, post_repo = setup_api_agent

    def mock_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        if topic.topic_id == topics[0].topic_id:
            return ResearchResult(research_id="r-fail", topic_id=topic.topic_id, status="failed", confidence=0.0, evidence_count=0)
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_usable_validation):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_usable_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_successful_draft):
                                res = client.post(
                                    f"/api/agent/{agent.agent_id}/workflow/run",
                                    json={"max_topics": 2, "editorial_threshold": 0.5}
                                )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PARTIAL_SUCCESS"
    assert "diagnostics" in data
    assert len(data["diagnostics"]) == 1
    assert data["diagnostics"][0]["topic_id"] == topics[0].topic_id


def test_workflow_inspection_endpoint_returns_diagnostics(setup_api_agent):
    """Test GET /api/agent/{agent_id}/workflow/{wf_id}/inspection exposes diagnostics."""
    agent, topics, client, _, _, topic_repo, wf_repo, post_repo = setup_api_agent

    def mock_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        if topic.topic_id == topics[0].topic_id:
            return ResearchResult(research_id="r-fail", topic_id=topic.topic_id, status="failed", confidence=0.0, evidence_count=0)
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_usable_validation):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_usable_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_successful_draft):
                                wf_res = run_agent_workflow(
                                    agent_id=agent.agent_id,
                                    config=WorkflowPolicy(max_topics=2, editorial_threshold=0.5),
                                    topic_repo=topic_repo,
                                    workflow_repo=wf_repo,
                                    post_repo=post_repo,
                                )

    res = client.get(f"/api/agent/{agent.agent_id}/workflow/{wf_res.workflow_id}/inspection")
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_id"] == wf_res.workflow_id
    assert "diagnostics" in data
    assert len(data["diagnostics"]) == 1
    assert data["diagnostics"][0]["topic_id"] == topics[0].topic_id


def test_workflow_history_endpoint_returns_diagnostics(setup_api_agent):
    """Test GET /api/agent/{agent_id}/workflows summary list exposes diagnostics."""
    agent, topics, client, _, _, topic_repo, wf_repo, post_repo = setup_api_agent

    def mock_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        if topic.topic_id == topics[0].topic_id:
            return ResearchResult(research_id="r-fail", topic_id=topic.topic_id, status="failed", confidence=0.0, evidence_count=0)
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics):
        with patch("app.services.workflow.orchestrator.evaluate_agent_topics", return_value=make_editorial_decisions(topics)):
            with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_research):
                with patch("app.services.workflow.orchestrator.validate_research", side_effect=mock_usable_validation):
                    with patch("app.services.workflow.orchestrator.synthesize_research", side_effect=mock_usable_synthesis):
                        with patch("app.services.workflow.orchestrator.build_content_brief", side_effect=mock_usable_brief):
                            with patch("app.services.workflow.orchestrator.generate_draft", side_effect=mock_successful_draft):
                                wf_res = run_agent_workflow(
                                    agent_id=agent.agent_id,
                                    config=WorkflowPolicy(max_topics=2, editorial_threshold=0.5),
                                    topic_repo=topic_repo,
                                    workflow_repo=wf_repo,
                                    post_repo=post_repo,
                                )

    res = client.get(f"/api/agent/{agent.agent_id}/workflows")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    item = data["items"][0]
    assert "diagnostics" in item
    assert len(item["diagnostics"]) == 1
