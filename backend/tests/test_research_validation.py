import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteEvidenceRepository,
    SQLiteResearchRepository,
    SQLiteTopicRepository,
)
from app.services.research.validation import (
    detect_redundancy,
    score_content_quality,
    score_evidence_completeness,
    score_source_diversity,
    score_source_quality,
    score_topic_relevance,
    validate_research,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_validation.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_research_setup(temp_db):
    """Fixture establishing Agent, Topic, and Research records in temporary database."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-val-test", "NOVA", "AI & Emerging Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic(
        topic_id="top-val-001",
        agent_id=agent.agent_id,
        title="Quantization and Distillation of Large Language Models",
        description="Technical paper on reducing LLM memory footprint and model weights.",
        source_url="https://arxiv.org/abs/2401.55555",
        source_name="ArXiv AI",
        status="selected",
    )

    research_repo = SQLiteResearchRepository(temp_db)
    research = research_repo.create_research(
        research_id="res-val-001",
        agent_id=agent.agent_id,
        topic_id=topic.topic_id,
        status="completed",
        confidence=0.85,
    )

    return topic, research


def test_high_quality_evidence_validation(temp_db, sample_research_setup):
    """1. Test that high-quality technical paper evidence passes validation."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    content = "Quantization and distillation of large language models allows 8-bit model weight compression. " * 15
    evidence_repo.create_evidence(
        evidence_id="ev-hq-01",
        research_id=research.research_id,
        source_url="https://arxiv.org/abs/2401.55555",
        source_name="ArXiv",
        title="Quantization and Distillation Paper",
        content=content,
        confidence=0.95,
    )

    result = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo)

    assert result.is_usable is True
    assert result.usable_evidence_count == 1
    assert result.rejected_evidence_count == 0
    assert result.evidence_items[0].is_valid is True
    assert result.evidence_items[0].score >= 0.80


def test_low_quality_evidence_rejection(temp_db, sample_research_setup):
    """2. Test that short boilerplate or 404 error content fails validation."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    evidence_repo.create_evidence(
        evidence_id="ev-lq-01",
        research_id=research.research_id,
        source_url="https://example.com/bad-page",
        source_name="Unknown Web",
        title="404 Not Found",
        content="404 Not Found. JavaScript required. Cookie policy all rights reserved navigation.",
        confidence=0.20,
    )

    result = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo)

    assert result.is_usable is False
    assert result.rejected_evidence_count == 1
    item = result.evidence_items[0]
    assert item.is_valid is False
    assert len(item.rejection_reasons) > 0
    assert any("content quality" in reason.lower() for reason in item.rejection_reasons)


def test_source_quality_scoring():
    """3. Test source quality scoring for academic vs tech vs unknown vs spam domains."""
    arxiv_score = score_source_quality("https://arxiv.org/abs/2401.0001", "ArXiv")
    tc_score = score_source_quality("https://techcrunch.com/article", "TechCrunch")
    gen_score = score_source_quality("https://random-blog.net/post", "Random Blog")
    spam_score = score_source_quality("https://clickbait-gossip-spam.com/news", "Spam Site")

    assert arxiv_score == 1.0
    assert tc_score == 0.85
    assert gen_score == 0.50
    assert spam_score == 0.20


def test_content_quality_scoring():
    """4. Test content quality scoring based on text volume and boilerplate."""
    long_content = "Substantial technical details about neural network architectures. " * 30
    moderate_content = "Moderate technical summary of LLM quantization benchmarks and evaluation metrics." * 2
    bp_content = "404 Not Found. Cookie policy JavaScript required."

    assert score_content_quality(long_content) == 0.95
    assert score_content_quality(moderate_content) == 0.45
    assert score_content_quality(bp_content) == 0.15


def test_topic_relevance_scoring():
    """5. Test topic relevance scoring via token overlap."""
    title = "Quantization of LLM Transformer Weights"
    desc = "Deep learning model compression algorithm."
    
    high_rel_content = "Quantization techniques for LLM transformer weights and model compression."
    off_topic_content = "Baking a delicious chocolate cake requires cocoa powder, flour, and sugar."

    rel_high = score_topic_relevance(title, desc, high_rel_content)
    rel_low = score_topic_relevance(title, desc, off_topic_content)

    assert rel_high >= 0.70
    assert rel_low <= 0.25


def test_evidence_completeness_scoring():
    """6. Test evidence completeness scoring based on total character volume."""
    ev_large = [
        type("Ev", (), {"content": "X" * 1000})(),
        type("Ev", (), {"content": "Y" * 1000})(),
    ]
    ev_small = [
        type("Ev", (), {"content": "Short text snippet."})(),
    ]

    assert score_evidence_completeness(ev_large) == 1.0
    assert score_evidence_completeness(ev_small) == 0.35


def test_source_diversity_scoring():
    """7. Test source diversity scoring based on distinct root domains."""
    ev_multi = [
        type("Ev", (), {"source_url": "https://arxiv.org/abs/1"})(),
        type("Ev", (), {"source_url": "https://techcrunch.com/news"})(),
        type("Ev", (), {"source_url": "https://github.com/repo"})(),
    ]
    ev_single = [
        type("Ev", (), {"source_url": "https://arxiv.org/abs/1"})(),
        type("Ev", (), {"source_url": "https://arxiv.org/abs/2"})(),
    ]

    assert score_source_diversity(ev_multi) == 1.0
    assert score_source_diversity(ev_single) == 0.50


def test_duplicate_evidence_detection(temp_db, sample_research_setup):
    """8. Test detection of duplicate evidence with identical source URL."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    content = "Identical content for quantization paper. " * 10
    evidence_repo.create_evidence("ev-dup-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Title 1", content)
    evidence_repo.create_evidence("ev-dup-2", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Title 1", content)

    result = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo)

    assert len(result.evidence_items) == 2
    assert result.evidence_items[0].is_valid is True
    assert result.evidence_items[1].is_valid is False
    assert "Redundant" in result.evidence_items[1].rejection_reasons[0]


def test_near_duplicate_content_detection():
    """9. Test near-duplicate content detection using text Jaccard similarity."""
    ev1 = type("Ev", (), {"evidence_id": "ev1", "source_url": "https://source1.com/a", "content": "Quantization of transformer LLM weights for efficient edge deployment and low latency inference."})()
    ev2 = type("Ev", (), {"evidence_id": "ev2", "source_url": "https://source2.com/b", "content": "Quantization of transformer LLM weights for efficient edge deployment and low latency inference."})()

    redundancy_map = detect_redundancy([ev1, ev2])
    assert redundancy_map["ev1"] is False
    assert redundancy_map["ev2"] is True


def test_configurable_validation_threshold(temp_db, sample_research_setup):
    """10. Test that changing the validation threshold alters usability outcome."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    content = "Moderate technical content about quantization techniques for neural networks. " * 5
    evidence_repo.create_evidence("ev-mod-1", research.research_id, "https://huggingface.co/blog/mod", "HF", "HF Blog", content)

    res_strict = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, threshold=0.90)
    res_lenient = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, threshold=0.50)

    assert res_strict.is_usable is False
    assert res_lenient.is_usable is True


def test_strong_research_classification(temp_db, sample_research_setup):
    """11. Test research classification as 'strong' with 2 high-quality distinct sources."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    content1 = "Quantization and distillation of large language models allows 8-bit model weight compression. " * 15
    content2 = "TechCrunch report on enterprise adoption of quantization frameworks for LLM inference. " * 15

    evidence_repo.create_evidence("ev-str-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper", content1)
    evidence_repo.create_evidence("ev-str-2", research.research_id, "https://techcrunch.com/quantization", "TechCrunch", "Article", content2)

    result = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo)

    assert result.quality_classification == "strong"
    assert result.is_usable is True
    assert result.needs_additional_research is False


def test_insufficient_research_classification(temp_db, sample_research_setup):
    """12. Test research classification as 'insufficient' when evidence quality/relevance is weak."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    short_off_topic = "Short note about cake recipes and cooking instructions."
    evidence_repo.create_evidence("ev-ins-1", research.research_id, "https://generic-blog.com/recipe", "Blog", "Recipe", short_off_topic)

    result = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo)

    assert result.quality_classification in ("insufficient", "unusable")
    assert result.needs_additional_research is True


def test_validation_explanations_rationales(temp_db, sample_research_setup):
    """13. Test that human-readable explanations and rationales are generated."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)
    evidence_repo.create_evidence("ev-rat-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Title", "Valid content " * 20)

    result = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo)

    assert result.rationale is not None
    assert "Research classification" in result.rationale
    assert "score:" in result.rationale


def test_existing_research_persistence_intact(temp_db, sample_research_setup):
    """14. Test that all evidence records remain persisted in SQLite even when failing validation."""
    topic, research = sample_research_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    # 1 valid item, 1 failing item
    evidence_repo.create_evidence("ev-pers-valid", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Valid", "Valid technical content " * 15)
    evidence_repo.create_evidence("ev-pers-invalid", research.research_id, "https://example.com/bad", "Bad", "Bad", "404 Not Found")

    result = validate_research(research.research_id, topic_repo=SQLiteTopicRepository(temp_db), research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo)

    # Analysis identifies 1 usable and 1 rejected
    assert result.usable_evidence_count == 1
    assert result.rejected_evidence_count == 1

    # Query SQLite directly to confirm NO rows were deleted!
    all_in_db = evidence_repo.list_evidence_by_research(research.research_id)
    assert len(all_in_db) == 2
    ids = [e.evidence_id for e in all_in_db]
    assert "ev-pers-valid" in ids
    assert "ev-pers-invalid" in ids
