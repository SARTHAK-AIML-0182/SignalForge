import sqlite3
import pytest
from app.db.database import get_connection, init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteTopicRepository,
    SQLiteResearchRepository,
    SQLiteEvidenceRepository,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_research.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_agent_and_topic(temp_db):
    """Fixture providing a persisted Agent and Topic in the temporary database."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-res-owner", "NOVA", "AI Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic(
        topic_id="topic-res-target",
        agent_id="agent-res-owner",
        title="Frontier Model Safety Standards",
        description="Analysis of safety evaluation frameworks for large language models.",
    )
    return agent, topic


def test_research_table_initialization(temp_db):
    """1. Test that the research table is initialized in SQLite."""
    conn = get_connection(temp_db)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='research';")
        row = cursor.fetchone()
        assert row is not None
        assert row["name"] == "research"
    finally:
        conn.close()


def test_evidence_table_initialization(temp_db):
    """2. Test that the evidence table is initialized in SQLite."""
    conn = get_connection(temp_db)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evidence';")
        row = cursor.fetchone()
        assert row is not None
        assert row["name"] == "evidence"
    finally:
        conn.close()


def test_create_research_record(temp_db, sample_agent_and_topic):
    """3. Test creating a research record."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)

    research = research_repo.create_research(
        research_id="res-001",
        agent_id=agent.agent_id,
        topic_id=topic.topic_id,
        status="pending",
        confidence=0.75,
    )

    assert research.research_id == "res-001"
    assert research.agent_id == agent.agent_id
    assert research.topic_id == topic.topic_id
    assert research.status == "pending"
    assert research.confidence == 0.75
    assert research.created_at is not None
    assert research.completed_at is None


def test_retrieve_research_record(temp_db, sample_agent_and_topic):
    """4. Test retrieving a research record by ID and by topic ID."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-002", agent.agent_id, topic.topic_id, "in_progress", 0.8)

    by_id = research_repo.get_research("res-002")
    assert by_id is not None
    assert by_id.research_id == "res-002"
    assert by_id.status == "in_progress"

    by_topic = research_repo.get_research_by_topic(topic.topic_id)
    assert by_topic is not None
    assert by_topic.research_id == "res-002"


def test_update_research_status(temp_db, sample_agent_and_topic):
    """5. Test updating research status."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-003", agent.agent_id, topic.topic_id, "pending", 0.5)

    updated = research_repo.update_research_status("res-003", "in_progress")
    assert updated is not None
    assert updated.status == "in_progress"


def test_update_research_confidence(temp_db, sample_agent_and_topic):
    """6. Test updating research confidence."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-004", agent.agent_id, topic.topic_id, "in_progress", 0.5)

    updated = research_repo.update_research_confidence("res-004", 0.92)
    assert updated is not None
    assert updated.confidence == 0.92


def test_complete_research_record(temp_db, sample_agent_and_topic):
    """7. Test completing a research record and setting completed_at timestamp."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-005", agent.agent_id, topic.topic_id, "in_progress", 0.8)

    completed = research_repo.complete_research("res-005", confidence=0.98, status="completed")
    assert completed is not None
    assert completed.status == "completed"
    assert completed.confidence == 0.98
    assert completed.completed_at is not None


def test_create_multiple_evidence_records(temp_db, sample_agent_and_topic):
    """8. Test creating multiple evidence records for one research investigation."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-006", agent.agent_id, topic.topic_id)

    evidence_repo = SQLiteEvidenceRepository(temp_db)
    ev1 = evidence_repo.create_evidence(
        evidence_id="ev-001",
        research_id="res-006",
        source_url="https://arxiv.org/abs/2401.00001",
        source_name="ArXiv",
        title="Safety Framework Paper",
        content="Technical description of safety benchmarks.",
        source_type="paper",
        confidence=0.9,
    )
    ev2 = evidence_repo.create_evidence(
        evidence_id="ev-002",
        research_id="res-006",
        source_url="https://techcrunch.com/safety-news",
        source_name="TechCrunch",
        title="Industry Safety News",
        content="News report on industry adoption of safety standards.",
        source_type="web",
        confidence=0.8,
    )

    assert ev1.evidence_id == "ev-001"
    assert ev2.evidence_id == "ev-002"
    assert ev1.research_id == "res-006"
    assert ev2.research_id == "res-006"


def test_retrieve_evidence_for_research(temp_db, sample_agent_and_topic):
    """9. Test retrieving evidence by evidence ID and by research ID."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-007", agent.agent_id, topic.topic_id)

    evidence_repo = SQLiteEvidenceRepository(temp_db)
    evidence_repo.create_evidence(
        evidence_id="ev-101",
        research_id="res-007",
        source_url="https://example.com/src1",
        source_name="Source One",
        title="Title One",
        content="Content One",
    )
    evidence_repo.create_evidence(
        evidence_id="ev-102",
        research_id="res-007",
        source_url="https://example.com/src2",
        source_name="Source Two",
        title="Title Two",
        content="Content Two",
    )

    by_id = evidence_repo.get_evidence("ev-101")
    assert by_id is not None
    assert by_id.title == "Title One"

    list_all = evidence_repo.list_evidence_by_research("res-007")
    assert len(list_all) == 2
    titles = [e.title for e in list_all]
    assert "Title One" in titles
    assert "Title Two" in titles


def test_agent_research_fk_relationship(temp_db, sample_agent_and_topic):
    """10. Test foreign key relationship and cascading deletion between agent and research."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-fk-agent", agent.agent_id, topic.topic_id)

    # Delete agent directly
    conn = get_connection(temp_db)
    try:
        with conn:
            conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent.agent_id,))
    finally:
        conn.close()

    assert research_repo.get_research("res-fk-agent") is None


def test_topic_research_fk_relationship(temp_db, sample_agent_and_topic):
    """11. Test foreign key relationship and cascading deletion between topic and research."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-fk-topic", agent.agent_id, topic.topic_id)

    # Delete topic directly
    conn = get_connection(temp_db)
    try:
        with conn:
            conn.execute("DELETE FROM topics WHERE topic_id = ?", (topic.topic_id,))
    finally:
        conn.close()

    assert research_repo.get_research("res-fk-topic") is None


def test_research_evidence_fk_relationship(temp_db, sample_agent_and_topic):
    """12. Test foreign key relationship and cascading deletion between research and evidence."""
    agent, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)
    research_repo.create_research("res-fk-ev", agent.agent_id, topic.topic_id)

    evidence_repo = SQLiteEvidenceRepository(temp_db)
    evidence_repo.create_evidence(
        evidence_id="ev-fk-target",
        research_id="res-fk-ev",
        source_url="https://example.com/fk",
        source_name="FK Source",
        title="FK Title",
        content="FK Content",
    )

    # Delete research directly
    conn = get_connection(temp_db)
    try:
        with conn:
            conn.execute("DELETE FROM research WHERE research_id = ?", ("res-fk-ev",))
    finally:
        conn.close()

    assert evidence_repo.get_evidence("ev-fk-target") is None


def test_invalid_agent_handling(temp_db, sample_agent_and_topic):
    """13. Test invalid/nonexistent agent ID raises IntegrityError due to FK constraint."""
    _, topic = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)

    with pytest.raises(sqlite3.IntegrityError):
        research_repo.create_research("res-bad-agent", "nonexistent-agent-id", topic.topic_id)


def test_invalid_topic_handling(temp_db, sample_agent_and_topic):
    """14. Test invalid/nonexistent topic ID raises IntegrityError due to FK constraint."""
    agent, _ = sample_agent_and_topic
    research_repo = SQLiteResearchRepository(temp_db)

    with pytest.raises(sqlite3.IntegrityError):
        research_repo.create_research("res-bad-topic", agent.agent_id, "nonexistent-topic-id")


def test_persistence_across_separate_connections(temp_db, sample_agent_and_topic):
    """15. Test research and evidence persistence across separate repository instances/connections."""
    agent, topic = sample_agent_and_topic

    res_repo1 = SQLiteResearchRepository(temp_db)
    res_repo1.create_research("res-persist", agent.agent_id, topic.topic_id, "completed", 0.95)

    ev_repo1 = SQLiteEvidenceRepository(temp_db)
    ev_repo1.create_evidence(
        evidence_id="ev-persist",
        research_id="res-persist",
        source_url="https://example.com/persist",
        source_name="Persist Source",
        title="Persist Title",
        content="Persist Content",
    )

    # Re-instantiate repositories against same database
    res_repo2 = SQLiteResearchRepository(temp_db)
    ev_repo2 = SQLiteEvidenceRepository(temp_db)

    res_retrieved = res_repo2.get_research("res-persist")
    assert res_retrieved is not None
    assert res_retrieved.confidence == 0.95
    assert res_retrieved.status == "completed"

    ev_retrieved = ev_repo2.get_evidence("ev-persist")
    assert ev_retrieved is not None
    assert ev_retrieved.title == "Persist Title"
    assert ev_retrieved.content == "Persist Content"
