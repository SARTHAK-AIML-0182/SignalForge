import pytest

from app.db.database import init_db
from app.repositories import (
    AgentPersonaData,
    SQLiteAgentRepository,
    SQLitePersonaRepository,
    TopicData,
)
from app.services.persona_alignment import evaluate_topic_alignment


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_persona.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_agent(temp_db):
    """Fixture setting up a valid agent in temporary DB."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-per-test", "NOVA", "AI & Emerging Tech")
    return agent, temp_db


def test_persona_creation_retrieval_and_update(setup_agent):
    """1-4. Test persona creation, retrieval, update, and persistence across repository re-instantiation."""
    agent, db_path = setup_agent
    repo1 = SQLitePersonaRepository(db_path)

    p1 = AgentPersonaData(
        agent_id=agent.agent_id,
        persona_name="NOVA Senior Tech Strategist",
        primary_domain="AI & Emerging Tech",
        secondary_domains=["Quantum Computing", "Robotics"],
        preferred_keywords=["neural", "transformer", "llm"],
        excluded_keywords=["crypto", "nft"],
        min_relevance_threshold=0.6,
    )
    saved = repo1.save_persona(p1)
    assert saved.persona_name == "NOVA Senior Tech Strategist"
    assert saved.min_relevance_threshold == 0.6

    # Re-instantiate repository (simulating process restart)
    repo2 = SQLitePersonaRepository(db_path)
    fetched = repo2.get_persona(agent.agent_id)
    assert fetched is not None
    assert fetched.persona_name == "NOVA Senior Tech Strategist"
    assert fetched.secondary_domains == ["Quantum Computing", "Robotics"]
    assert fetched.preferred_keywords == ["neural", "transformer", "llm"]

    # Update persona
    fetched.min_relevance_threshold = 0.7
    fetched.preferred_keywords.append("robotics")
    updated = repo2.save_persona(fetched)
    assert updated.min_relevance_threshold == 0.7

    repo3 = SQLitePersonaRepository(db_path)
    re_fetched = repo3.get_persona(agent.agent_id)
    assert re_fetched.min_relevance_threshold == 0.7
    assert "robotics" in re_fetched.preferred_keywords


def test_legacy_agent_default_persona_behavior(setup_agent):
    """5. Test that legacy agent without explicit persona record receives safe default persona."""
    agent, db_path = setup_agent
    repo = SQLitePersonaRepository(db_path)

    default_persona = repo.get_persona(agent.agent_id)
    assert default_persona is not None
    assert default_persona.persona_name == "NOVA"
    assert default_persona.primary_domain == "AI & Emerging Tech"
    assert default_persona.min_relevance_threshold == 0.5


def test_topic_domain_alignment():
    """7. Test primary domain, secondary domain, and baseline relevance scoring."""
    persona = AgentPersonaData(
        agent_id="a1",
        persona_name="Test",
        primary_domain="Artificial Intelligence",
        secondary_domains=["Machine Learning", "Data Science"],
        min_relevance_threshold=0.5,
    )

    t_primary = TopicData("t1", "a1", "Breakthrough in Artificial Intelligence Research", "Desc", "https://ex.com", "Tech")
    dec_primary = evaluate_topic_alignment(t_primary, persona)
    assert dec_primary.aligned is True
    assert dec_primary.relevance_score >= 0.70  # base 0.20 + primary 0.50

    t_sec = TopicData("t2", "a1", "New Machine Learning Algorithm Released", "Desc", "https://ex.com", "Tech")
    dec_sec = evaluate_topic_alignment(t_sec, persona)
    assert dec_sec.aligned is True
    assert dec_sec.relevance_score >= 0.60  # base 0.20 + sec 0.40


def test_keyword_and_category_alignment():
    """8, 10. Test preferred keyword and preferred category alignment scoring bonuses."""
    persona = AgentPersonaData(
        agent_id="a1",
        persona_name="Test",
        primary_domain="AI",
        preferred_keywords=["transformer", "deepseek"],
        preferred_categories=["tech", "research"],
        min_relevance_threshold=0.5,
    )

    t = TopicData("t3", "a1", "DeepSeek releases new transformer AI model for research", "Tech news", "https://ex.com", "Tech")
    dec = evaluate_topic_alignment(t, persona)
    assert dec.aligned is True
    assert "transformer" in dec.matched_keywords
    assert "deepseek" in dec.matched_keywords
    assert "tech" in dec.matched_categories or "research" in dec.matched_categories


def test_excluded_keyword_and_category_rejection():
    """9, 11. Test that excluded keywords or categories trigger deterministic rejection."""
    persona = AgentPersonaData(
        agent_id="a1",
        persona_name="Test",
        primary_domain="AI",
        excluded_keywords=["crypto", "memecoin"],
        excluded_categories=["gambling"],
        min_relevance_threshold=0.5,
    )

    t_crypto = TopicData("t4", "a1", "AI used for crypto trading and memecoin analysis", "Desc", "https://ex.com", "Tech")
    dec = evaluate_topic_alignment(t_crypto, persona)
    assert dec.aligned is False
    assert "crypto" in dec.excluded_keywords or "memecoin" in dec.excluded_keywords
    assert "REJECTED" in dec.rationale


def test_relevance_threshold_behavior():
    """12. Test that topics falling below min_relevance_threshold are rejected."""
    persona = AgentPersonaData(
        agent_id="a1",
        persona_name="Test",
        primary_domain="Robotics",
        min_relevance_threshold=0.8,  # High threshold
    )

    t_unrelated = TopicData("t5", "a1", "Unrelated General News Article", "Desc", "https://ex.com", "News")
    dec = evaluate_topic_alignment(t_unrelated, persona)
    assert dec.aligned is False
    assert dec.relevance_score < 0.8
    assert "below minimum threshold" in dec.rationale


def test_deterministic_alignment_results():
    """13. Test that persona evaluation produces identical results for identical inputs."""
    persona = AgentPersonaData(agent_id="a1", persona_name="Test", primary_domain="AI")
    topic = TopicData("t6", "a1", "Autonomous AI Agents", "Desc", "https://ex.com", "Tech")

    dec1 = evaluate_topic_alignment(topic, persona)
    dec2 = evaluate_topic_alignment(topic, persona)
    assert dec1.to_dict() == dec2.to_dict()
