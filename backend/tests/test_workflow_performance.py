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
from app.services.workflow import WorkflowPolicy, run_agent_workflow


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_performance.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_multi_topic_agent(temp_db):
    """Fixture setting up agent with 5 topics for batch testing."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)
    post_repo = SQLitePostRepository(temp_db)
    persona_repo = SQLitePersonaRepository(temp_db)

    agent = agent_repo.save_agent("agent-perf-001", "NOVA", "AI & Emerging Tech")
    topics = [
        topic_repo.create_topic(
            f"top-perf-{i:03d}",
            agent.agent_id,
            f"Topic Title {i:03d} for Autonomous AI Research",
            f"Description for topic {i:03d}",
            f"https://example.com/topic-{i}",
            "Tech Daily"
        )
        for i in range(1, 6)
    ]

    app.dependency_overrides[get_agent_repository] = lambda: agent_repo
    app.dependency_overrides[get_workflow_repository] = lambda: wf_repo
    app.dependency_overrides[get_post_repository] = lambda: post_repo
    app.dependency_overrides[get_persona_repository] = lambda: persona_repo

    client = TestClient(app)
    yield agent, topics, client, temp_db, agent_repo, topic_repo, wf_repo, post_repo
    app.dependency_overrides.clear()


def test_batch_topic_retrieval(setup_multi_topic_agent):
    """1. Test get_topics_by_ids batch querying in TopicRepository."""
    _, topics, _, _, _, topic_repo, _, _ = setup_multi_topic_agent
    topic_ids = [t.topic_id for t in topics]

    batch_fetched = topic_repo.get_topics_by_ids(topic_ids)
    assert len(batch_fetched) == len(topics)
    assert [t.topic_id for t in batch_fetched] == topic_ids


def test_multi_topic_batch_execution_and_deterministic_ordering(setup_multi_topic_agent):
    """2. Test multi-topic batch execution preserves exact deterministic ordering and stage sequence."""
    agent, topics, _, _, _, topic_repo, wf_repo, post_repo = setup_multi_topic_agent

    def mock_success_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.85, evidence_count=2)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics):
        with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_success_research):
            result = run_agent_workflow(
                agent_id=agent.agent_id,
                config=WorkflowPolicy(max_topics=5, editorial_threshold=0.5),
                topic_repo=topic_repo,
                workflow_repo=wf_repo,
                post_repo=post_repo,
            )

    assert result.status in ("SUCCESS", "PARTIAL_SUCCESS", "NO_CONTENT")
    assert set(result.selected_topic_ids) == {t.topic_id for t in topics}
    assert len(result.selected_topic_ids) == 5

    # Verify stage order is deterministic
    stage_names = [s.stage_name for s in result.stages]
    assert stage_names[0] == "topic_discovery"
    assert stage_names[1] == "persona_alignment"
    assert stage_names[2] == "editorial_evaluation"

    # Verify traceability mapping contains all topics
    assert "persona_alignment" in result.traceability
    for t in topics:
        assert t.topic_id in result.traceability


def test_mixed_topic_success_failure_isolation(setup_multi_topic_agent):
    """3. Test failure isolation in multi-topic execution (failure in topic 2 does not affect topic 1 or 3)."""
    agent, topics, _, _, _, topic_repo, wf_repo, post_repo = setup_multi_topic_agent

    # Fail research for topic 2
    def mock_research(topic, **kwargs):
        from app.services.research.engine import ResearchResult
        if topic.topic_id == topics[1].topic_id:
            return ResearchResult(research_id="r-fail", topic_id=topic.topic_id, status="failed", confidence=0.0, evidence_count=0)
        return ResearchResult(research_id=f"res-{topic.topic_id}", topic_id=topic.topic_id, status="completed", confidence=0.9, evidence_count=2)

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics):
        with patch("app.services.workflow.orchestrator.research_topic", side_effect=mock_research):
            result = run_agent_workflow(
                agent_id=agent.agent_id,
                config=WorkflowPolicy(max_topics=5, editorial_threshold=0.5),
                topic_repo=topic_repo,
                workflow_repo=wf_repo,
                post_repo=post_repo,
            )

    assert result.status == "FAILED"
    # Verify topic 2 research failed stage recorded, but topic 1 research succeeded (failure isolation)
    res_stages = [s for s in result.stages if s.stage_name == f"research_{topics[1].topic_id}"]
    assert len(res_stages) == 1
    assert res_stages[0].status == "FAILED"

    # Verify topic 1 research succeeded
    res1_stages = [s for s in result.stages if s.stage_name == f"research_{topics[0].topic_id}"]
    assert len(res1_stages) == 1
    assert res1_stages[0].status == "SUCCEEDED"


def test_process_restart_persistence_for_multi_topic_workflow(setup_multi_topic_agent):
    """4. Test process restart persistence for multi-topic batch workflow results."""
    agent, topics, _, db_path, _, topic_repo, wf_repo, post_repo = setup_multi_topic_agent

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=topics[:3]):
        res1 = run_agent_workflow(
            agent_id=agent.agent_id,
            config=WorkflowPolicy(max_topics=3),
            topic_repo=topic_repo,
            workflow_repo=wf_repo,
            post_repo=post_repo,
        )

    # Re-instantiate repository (simulating app restart)
    wf_repo2 = SQLiteWorkflowRepository(db_path)
    loaded = wf_repo2.get_workflow(res1.workflow_id)
    assert loaded is not None
    assert loaded.workflow_id == res1.workflow_id
    assert len(loaded.stages) == len(res1.stages)
    assert loaded.selected_topic_ids == res1.selected_topic_ids
