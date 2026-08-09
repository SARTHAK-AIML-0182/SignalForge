import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteEvidenceRepository,
    SQLiteResearchRepository,
    SQLiteTopicRepository,
)
from app.services.research.content_brief import build_content_brief


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_brief.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_brief_setup(temp_db):
    """Fixture establishing Agent, Topic, and Research records in temporary database."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-brief-test", "NOVA", "AI & Emerging Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic(
        topic_id="top-brief-001",
        agent_id=agent.agent_id,
        title="Quantization and Distillation of Large Language Models",
        description="Technical paper on reducing LLM memory footprint and model weights.",
        source_url="https://arxiv.org/abs/2401.55555",
        source_name="ArXiv AI",
        status="selected",
    )

    research_repo = SQLiteResearchRepository(temp_db)
    research = research_repo.create_research(
        research_id="res-brief-001",
        agent_id=agent.agent_id,
        topic_id=topic.topic_id,
        status="completed",
        confidence=0.90,
    )

    return agent, topic, research


def test_content_brief_from_strong_research(temp_db, sample_brief_setup):
    """1. Test Content Brief creation from strong validated research with 2 distinct sources."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("Substantial technical paper analysis detailing architecture improvements for neural networks. " * 12)
    c2 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("TechCrunch report confirms enterprise adoption of quantization frameworks for LLM inference. " * 12)

    evidence_repo.create_evidence("ev-br-str-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper 1", c1, confidence=0.95)
    evidence_repo.create_evidence("ev-br-str-2", research.research_id, "https://techcrunch.com/quantization", "TechCrunch", "Article 2", c2, confidence=0.90)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert result.is_usable is True
    assert len(result.claims) >= 1
    assert result.confidence >= 0.80
    assert "VALIDATED CONTENT BRIEF" in result.rationale


def test_content_brief_from_acceptable_research(temp_db, sample_brief_setup):
    """2. Test Content Brief creation from acceptable research with 1 tech source."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization techniques for LLM transformer model weights reduce GPU memory requirements significantly. " + ("Comprehensive benchmarks for neural network compression. " * 8)
    evidence_repo.create_evidence("ev-br-acc-1", research.research_id, "https://huggingface.co/blog/quant", "Hugging Face", "Blog", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert result.is_usable is True
    assert len(result.claims) >= 1


def test_unusable_research_produces_non_usable_brief(temp_db, sample_brief_setup):
    """3. Test refusal to produce usable brief when underlying research is 'unusable'."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    evidence_repo.create_evidence("ev-br-bad-1", research.research_id, "https://example.com/404", "Bad", "404", "404 Not Found. JavaScript required. Cookie policy all rights reserved navigation.")

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert result.is_usable is False
    assert len(result.claims) == 0
    assert "REFUSED" in result.rationale


def test_insufficient_research_is_clearly_marked(temp_db, sample_brief_setup):
    """4. Test incomplete brief handling when underlying research is 'insufficient'."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    moderate_content = "Quantization and distillation of large language models research summary. " * 4
    evidence_repo.create_evidence("ev-br-ins-1", research.research_id, "https://random-blog.net/note", "Blog", "Note", moderate_content)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert result.is_usable is False
    assert "INCOMPLETE" in result.rationale


def test_content_angle_generation(temp_db, sample_brief_setup):
    """5. Test deterministic content angle generation."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization and distillation of large language models improves memory efficiency. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-ang-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert "Quantization and Distillation of Large Language Models" in result.angle
    assert "Technical analysis" in result.angle


def test_audience_context_generation(temp_db, sample_brief_setup):
    """6. Test audience/context generation from persona identity."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-aud-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert result.audience["target_persona"] == "NOVA"
    assert result.audience["primary_domain"] == "AI & Emerging Tech"
    assert "Technical" in result.audience["technical_depth"]


def test_claim_extraction_from_synthesized_findings(temp_db, sample_brief_setup):
    """7. Test supported claims mapping from synthesized findings."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-ext-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert len(result.claims) >= 1
    assert "quantization" in result.claims[0].claim_text.lower()


def test_claim_to_finding_traceability(temp_db, sample_brief_setup):
    """8. Test claim-to-finding traceability."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-trf-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    for claim in result.claims:
        assert len(claim.finding_ids) > 0
        assert claim.finding_ids[0].startswith("find-")


def test_claim_to_evidence_traceability(temp_db, sample_brief_setup):
    """9. Test claim-to-evidence traceability."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-tre-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    for claim in result.claims:
        assert len(claim.evidence_ids) > 0
        assert "ev-br-tre-1" in claim.evidence_ids


def test_claim_to_source_traceability(temp_db, sample_brief_setup):
    """10. Test claim-to-source URL traceability."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-trs-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    for claim in result.claims:
        assert len(claim.source_urls) > 0
        assert "https://arxiv.org/abs/2401.55555" in claim.source_urls


def test_rejected_evidence_cannot_appear_in_brief(temp_db, sample_brief_setup):
    """11. Test that evidence rejected during validation never appears in brief claims."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c_valid = "Quantization of LLM transformer weights reduces memory overhead. " + ("Valid technical paper evaluation of deep learning. " * 8)
    c_rejected = "404 Not Found. Cookie policy JavaScript required."

    evidence_repo.create_evidence("ev-br-val-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Valid", c_valid, confidence=0.85)
    evidence_repo.create_evidence("ev-br-rej-1", research.research_id, "https://example.com/404", "Bad", "Bad", c_rejected, confidence=0.10)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    all_brief_ev_ids = [ev_id for c in result.claims for ev_id in c.evidence_ids]
    assert "ev-br-val-1" in all_brief_ev_ids
    assert "ev-br-rej-1" not in all_brief_ev_ids


def test_research_limitations_preserved(temp_db, sample_brief_setup):
    """12. Test that synthesis limitations are preserved in the Content Brief."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-lim-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert len(result.limitations) > 0
    assert any("Low source diversity" in lim for lim in result.limitations)


def test_writing_constraints_present_and_structured(temp_db, sample_brief_setup):
    """13. Test that 6 structured mandatory writing constraints are present."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-cst-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert len(result.constraints) == 6
    for rule in result.constraints:
        assert rule.is_mandatory is True
        assert rule.rule_id.startswith("rule-")
        assert len(rule.description) > 10


def test_confidence_remains_bounded(temp_db, sample_brief_setup):
    """14. Test that brief confidence and claim confidences remain bounded between 0.0 and 1.0."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-cnf-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    result = build_content_brief(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
        agent_repo=SQLiteAgentRepository(temp_db),
    )

    assert 0.0 <= result.confidence <= 1.0
    for claim in result.claims:
        assert 0.0 <= claim.confidence <= 1.0


def test_deterministic_output_across_runs(temp_db, sample_brief_setup):
    """15. Test reproducible output across repeated brief generation calls."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-br-det-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1, confidence=0.85)

    b1 = build_content_brief(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db), agent_repo=SQLiteAgentRepository(temp_db))
    b2 = build_content_brief(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db), agent_repo=SQLiteAgentRepository(temp_db))

    assert b1.angle == b2.angle
    assert b1.confidence == b2.confidence
    assert len(b1.claims) == len(b2.claims)
    assert b1.claims[0].claim_text == b2.claims[0].claim_text


def test_existing_persistence_intact(temp_db, sample_brief_setup):
    """16. Test that generating Content Brief leaves all SQLite database records untouched."""
    agent, topic, research = sample_brief_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)
    evidence_repo.create_evidence("ev-br-stay-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", "Quantization of LLM transformer weights reduces memory. " + ("Valid content " * 10), confidence=0.85)

    build_content_brief(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db), agent_repo=SQLiteAgentRepository(temp_db))

    # Verify database records remain untouched
    db_res = SQLiteResearchRepository(temp_db).get_research(research.research_id)
    assert db_res is not None
    assert db_res.status == "completed"

    db_evs = SQLiteEvidenceRepository(temp_db).list_evidence_by_research(research.research_id)
    assert len(db_evs) == 1
    assert db_evs[0].evidence_id == "ev-br-stay-1"
