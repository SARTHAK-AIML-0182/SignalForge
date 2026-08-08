import sqlite3
import pytest
from app.db.database import get_connection, init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteTopicRepository,
    SQLitePostRepository,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_signalforge.db"
    init_db(db_file)
    return db_file


def test_database_initialization(temp_db):
    """Test that database tables are initialized properly."""
    conn = get_connection(temp_db)
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        assert "agents" in tables
        assert "topics" in tables
        assert "posts" in tables
    finally:
        conn.close()


def test_create_and_retrieve_agent(temp_db):
    """Test creating an agent and retrieving it from SQLite."""
    agent_repo = SQLiteAgentRepository(temp_db)
    
    agent = agent_repo.save_agent(
        agent_id="agent-001",
        name="NOVA",
        domain="AI & Emerging Technology",
        status="active"
    )
    
    assert agent.agent_id == "agent-001"
    assert agent.name == "NOVA"
    assert agent.domain == "AI & Emerging Technology"
    assert agent.status == "active"
    assert agent.initialized_at is not None

    retrieved = agent_repo.get_agent("agent-001")
    assert retrieved is not None
    assert retrieved.agent_id == "agent-001"
    assert retrieved.persona_name == "NOVA"
    assert retrieved.persona_domain == "AI & Emerging Technology"
    assert retrieved.status == "active"
    assert retrieved.initialized_at == agent.initialized_at


def test_agent_persistence(temp_db):
    """Test that agent data persists across new repository instances / connections."""
    repo1 = SQLiteAgentRepository(temp_db)
    repo1.save_agent(
        agent_id="agent-persist",
        name="PERSIST_BOT",
        domain="Persistence",
        status="active"
    )

    # Re-instantiate repository pointing to same database
    repo2 = SQLiteAgentRepository(temp_db)
    retrieved = repo2.get_agent("agent-persist")
    
    assert retrieved is not None
    assert retrieved.agent_id == "agent-persist"
    assert retrieved.name == "PERSIST_BOT"
    assert retrieved.domain == "Persistence"


def test_create_and_retrieve_topic(temp_db):
    """Test creating and retrieving a topic in SQLite."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent_repo.save_agent("agent-topic-owner", "TopicBot", "Research")

    topic_repo = SQLiteTopicRepository(temp_db)
    created_topic = topic_repo.create_topic(
        topic_id="topic-101",
        agent_id="agent-topic-owner",
        title="Breakthrough in Quantum Computing",
        description="Detailed analysis of fault-tolerant qubits.",
        source_url="https://example.com/quantum",
        source_name="Quantum Tech Daily",
        editorial_score=8.5,
        status="discovered"
    )

    assert created_topic.topic_id == "topic-101"
    assert created_topic.editorial_score == 8.5

    retrieved_topic = topic_repo.get_topic("topic-101")
    assert retrieved_topic is not None
    assert retrieved_topic.title == "Breakthrough in Quantum Computing"
    assert retrieved_topic.source_name == "Quantum Tech Daily"
    assert retrieved_topic.source_url == "https://example.com/quantum"

    topics_list = topic_repo.list_topics_by_agent("agent-topic-owner")
    assert len(topics_list) == 1
    assert topics_list[0].topic_id == "topic-101"


def test_create_and_retrieve_post(temp_db):
    """Test creating and retrieving a post with structured sources in SQLite."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent_repo.save_agent("agent-post-owner", "PostWriter", "News")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic_repo.create_topic("topic-for-post", "agent-post-owner", "AI Ethics")

    post_repo = SQLitePostRepository(temp_db)
    sources_data = [
        {"url": "https://arxiv.org/abs/1234.5678", "name": "arXiv Preprint"},
        "https://techcrunch.com/article"
    ]
    
    created_post = post_repo.create_post(
        post_id="post-202",
        agent_id="agent-post-owner",
        topic_id="topic-for-post",
        text="AI safety guidelines updated for 2026.",
        rationale="High societal impact topic.",
        sources=sources_data,
        editorial_score=9.2
    )

    assert created_post.post_id == "post-202"
    assert created_post.sources == sources_data

    retrieved_post = post_repo.get_post("post-202")
    assert retrieved_post is not None
    assert retrieved_post.text == "AI safety guidelines updated for 2026."
    assert retrieved_post.rationale == "High societal impact topic."
    assert retrieved_post.sources == sources_data
    assert retrieved_post.editorial_score == 9.2

    agent_posts = post_repo.list_posts_by_agent("agent-post-owner")
    assert len(agent_posts) == 1
    assert agent_posts[0].post_id == "post-202"
