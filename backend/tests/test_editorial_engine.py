from datetime import datetime, timedelta, timezone
import pytest

from app.db.database import init_db
from app.repositories import SQLiteAgentRepository, SQLiteTopicRepository, TopicData
from app.services.editorial import (
    EditorialDecision,
    evaluate_agent_topics,
    evaluate_topic,
    score_novelty,
    score_persona_alignment,
    score_potential_impact,
    score_relevance,
    score_technical_significance,
    score_timeliness,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_editorial.db"
    init_db(db_file)
    return db_file


def test_high_value_topic_selection():
    """Test that a high-impact AI research/agent topic is selected."""
    topic = TopicData(
        topic_id="top-high-val",
        agent_id="agent-nova",
        title="Breakthrough in Autonomous AI Agent Frameworks for Complex Codebases",
        description="New open-source LLM agent architecture achieves SOTA benchmarks in code generation and security audits.",
        source_url="https://example.com/ai-breakthrough",
        source_name="ArXiv AI",
        discovered_at=datetime.now(timezone.utc).isoformat()
    )

    decision = evaluate_topic(topic, threshold=6.5)

    assert decision.decision == "selected"
    assert decision.total_score >= 6.5
    assert decision.factors["relevance"] >= 7.0
    assert decision.factors["technical_significance"] >= 7.0
    assert "SELECTED" in decision.rationale


def test_low_value_topic_rejection():
    """Test that a low-value corporate/marketing topic is rejected."""
    topic = TopicData(
        topic_id="top-low-val",
        agent_id="agent-nova",
        title="Company X Unveils New Logo and Quarterly Earnings Report",
        description="Stock price surges after PR announcement about new corporate branding and executive hires.",
        source_url="https://example.com/corporate-pr",
        source_name="Generic News",
        discovered_at=datetime.now(timezone.utc).isoformat()
    )

    decision = evaluate_topic(topic, threshold=6.5)

    assert decision.decision == "rejected"
    assert decision.total_score < 6.5
    assert "REJECTED" in decision.rationale


def test_domain_relevance_scoring():
    """Test domain relevance scoring between AI tech stories vs non-AI stories."""
    ai_rel = score_relevance(
        "Deep Learning Attention Mechanism Optimization for LLM Inference",
        "Improving transformer latency using FlashAttention."
    )
    non_ai_rel = score_relevance(
        "Celebrity Red Carpet Fashion Review at Annual Gala",
        "Top dressed stars at the movie premiere."
    )

    assert ai_rel >= 8.0
    assert non_ai_rel <= 2.0


def test_timeliness_scoring():
    """Test timeliness scoring based on discovery timestamp age."""
    now_iso = datetime.now(timezone.utc).isoformat()
    old_iso = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    fresh_score = score_timeliness(now_iso)
    old_score = score_timeliness(old_iso)

    assert fresh_score >= 9.0
    assert old_score <= 4.5
    assert fresh_score > old_score


def test_technical_significance_scoring():
    """Test technical significance scoring for research papers vs generic podcasts."""
    tech_score = score_technical_significance(
        "Quantization and Distillation of Transformer Model Weights for On-Device Inference",
        "Reducing 8-bit model memory footprint with zero accuracy loss."
    )
    promo_score = score_technical_significance(
        "Company Launches Podcast Episode 5: Unveils New Brand Logo",
        "Discussion on executive hires and merch discounts."
    )

    assert tech_score >= 8.0
    assert promo_score <= 4.0
    assert tech_score > promo_score


def test_novelty_handling():
    """Test that a topic highly similar to an existing evaluated topic gets low novelty."""
    existing = [
        TopicData(
            topic_id="top-prev",
            agent_id="agent-nova",
            title="FlashAttention-3: Ultra-Fast Attention for Large Language Models",
            description="Optimizing VLM and LLM attention mechanisms on GPUs."
        )
    ]

    dup_nov = score_novelty(
        "FlashAttention-3: Ultra-Fast Attention for Large Language Models",
        "Optimizing VLM and LLM attention mechanisms on GPUs.",
        existing_topics=existing
    )
    new_nov = score_novelty(
        "Quantum Computing Superconducting Qubit Breakthrough",
        "Fault tolerant quantum error correction.",
        existing_topics=existing
    )

    assert dup_nov <= 2.0
    assert new_nov >= 9.0


def test_persona_alignment():
    """Test persona alignment scoring against NOVA's editorial philosophy."""
    align_high = score_persona_alignment(
        "Deploying Open-Source AI Infrastructure for Developer Tooling",
        "Framework for building and securing autonomous agents."
    )
    assert align_high >= 7.5


def test_configurable_publication_threshold():
    """Test that changing publication threshold alters selection outcome."""
    topic = TopicData(
        topic_id="top-borderline",
        agent_id="agent-nova",
        title="Moderate AI Tooling Update for Developers",
        description="Minor release with updated CLI helper functions.",
        source_url="https://example.com/mod",
        discovered_at=datetime.now(timezone.utc).isoformat()
    )

    dec_strict = evaluate_topic(topic, threshold=8.0)
    dec_lenient = evaluate_topic(topic, threshold=4.0)

    assert dec_strict.decision == "rejected"
    assert dec_lenient.decision == "selected"


def test_persistence_of_editorial_decisions(temp_db):
    """Test that both selected and rejected decisions are saved in SQLite with score and rationale."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent_repo.save_agent("agent-persist-test", "NOVA", "AI & Emerging Technology")

    topic_repo = SQLiteTopicRepository(temp_db)

    # Insert 1 high-value topic and 1 low-value topic
    topic_repo.create_topic(
        topic_id="top-sel-1",
        agent_id="agent-persist-test",
        title="Frontier AI Model Safety Audit and Vulnerability Framework",
        description="Technical paper on securing autonomous AI agents against prompt injection."
    )
    topic_repo.create_topic(
        topic_id="top-rej-1",
        agent_id="agent-persist-test",
        title="Celebrity Stock Portfolio Surges After PR Announcement",
        description="Quarterly earnings and promotional merch discounts."
    )

    decisions = evaluate_agent_topics("agent-persist-test", repo=topic_repo, threshold=6.5)

    assert len(decisions) == 2

    sel_topic = topic_repo.get_topic("top-sel-1")
    assert sel_topic is not None
    assert sel_topic.status == "selected"
    assert sel_topic.editorial_score >= 6.5
    assert sel_topic.rationale is not None
    assert "SELECTED" in sel_topic.rationale

    rej_topic = topic_repo.get_topic("top-rej-1")
    assert rej_topic is not None
    assert rej_topic.status == "rejected"
    assert rej_topic.editorial_score < 6.5
    assert rej_topic.rationale is not None
    assert "REJECTED" in rej_topic.rationale


def test_previously_evaluated_topics_not_reselected(temp_db):
    """Test that previously evaluated topics (status='selected' or 'rejected') are skipped in future evaluation runs."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent_repo.save_agent("agent-repeat-test", "NOVA", "AI & Emerging Technology")

    topic_repo = SQLiteTopicRepository(temp_db)

    # Pre-populate 1 already selected topic and 1 un-evaluated topic
    topic_repo.create_topic(
        topic_id="top-already-done",
        agent_id="agent-repeat-test",
        title="Previous Frontier AI Research Paper",
        description="Already evaluated in prior run.",
        editorial_score=8.5,
        status="selected",
        rationale="SELECTED previously"
    )
    topic_repo.create_topic(
        topic_id="top-new-disc",
        agent_id="agent-repeat-test",
        title="New Open-Source AI Agent Framework",
        description="Freshly discovered topic awaiting evaluation.",
        status="discovered"
    )

    decisions = evaluate_agent_topics("agent-repeat-test", repo=topic_repo, threshold=6.5)

    # Only 1 decision should be returned (the un-evaluated topic)
    assert len(decisions) == 1
    assert decisions[0].topic_id == "top-new-disc"
