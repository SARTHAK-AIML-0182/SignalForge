import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteEvidenceRepository,
    SQLiteResearchRepository,
    SQLiteTopicRepository,
)
from app.services.research.synthesis import synthesize_research


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_synthesis.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_synthesis_setup(temp_db):
    """Fixture establishing Agent, Topic, and Research records in temporary database."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-syn-test", "NOVA", "AI & Emerging Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic(
        topic_id="top-syn-001",
        agent_id=agent.agent_id,
        title="Quantization and Distillation of Large Language Models",
        description="Technical paper on reducing LLM memory footprint and model weights.",
        source_url="https://arxiv.org/abs/2401.55555",
        source_name="ArXiv AI",
        status="selected",
    )

    research_repo = SQLiteResearchRepository(temp_db)
    research = research_repo.create_research(
        research_id="res-syn-001",
        agent_id=agent.agent_id,
        topic_id=topic.topic_id,
        status="completed",
        confidence=0.90,
    )

    return topic, research


def test_synthesis_from_strong_validated_research(temp_db, sample_synthesis_setup):
    """1. Test synthesis from strong validated research with 2 distinct high-quality sources."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("Substantial technical paper analysis detailing architecture improvements for neural networks. " * 12)
    c2 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("TechCrunch report confirms enterprise adoption of quantization frameworks for LLM inference. " * 12)

    evidence_repo.create_evidence("ev-str-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper 1", c1, confidence=0.95)
    evidence_repo.create_evidence("ev-str-2", research.research_id, "https://techcrunch.com/quantization", "TechCrunch", "Article 2", c2, confidence=0.90)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    assert result.is_usable is True
    assert result.quality_classification == "strong"
    assert len(result.findings) >= 1
    assert result.source_diversity_count == 2
    assert "arxiv.org" in result.distinct_domains
    assert "techcrunch.com" in result.distinct_domains


def test_synthesis_from_acceptable_validated_research(temp_db, sample_synthesis_setup):
    """2. Test synthesis from acceptable validated research with 1 tech source."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization techniques for LLM transformer model weights reduce GPU memory requirements significantly. " + ("Comprehensive benchmarks for neural network compression. " * 8)
    evidence_repo.create_evidence("ev-acc-1", research.research_id, "https://huggingface.co/blog/quant", "Hugging Face", "Blog", c1)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    assert result.is_usable is True
    assert result.quality_classification == "acceptable"
    assert len(result.findings) >= 1


def test_refusal_for_unusable_research(temp_db, sample_synthesis_setup):
    """3. Test refusal to produce usable synthesis when research validation yields 'unusable'."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    # Boilerplate / 404 text fails validation
    evidence_repo.create_evidence("ev-bad-1", research.research_id, "https://example.com/404", "Bad", "404", "404 Not Found. JavaScript required. Cookie policy all rights reserved navigation.")

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    assert result.is_usable is False
    assert result.quality_classification == "unusable"
    assert len(result.findings) == 0
    assert "REFUSED" in result.rationale


def test_insufficient_research_handling(temp_db, sample_synthesis_setup):
    """4. Test incomplete synthesis handling when research is classified as 'insufficient'."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    # Content length 150 chars gives score between 0.40 and threshold 0.65 -> insufficient
    moderate_content = "Quantization and distillation of large language models research summary. " * 3
    evidence_repo.create_evidence("ev-ins-1", research.research_id, "https://random-blog.net/note", "Blog", "Note", moderate_content)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    assert result.is_usable is False
    assert result.quality_classification in ("insufficient", "unusable")
    assert any("INSUFFICIENT" in lim.upper() or "UNUSABLE" in lim.upper() for lim in result.limitations)


def test_extraction_of_topic_relevant_findings(temp_db, sample_synthesis_setup):
    """5. Test extraction of topic-relevant sentences as findings."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization and distillation of large language models improves memory efficiency and inference speed. " + ("Additional technical paper notes on transformer optimization. " * 8)
    evidence_repo.create_evidence("ev-rel-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper", c1)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    assert len(result.findings) >= 1
    finding_text = result.findings[0].text.lower()
    assert "quantization" in finding_text or "language models" in finding_text


def test_finding_traceability_to_evidence_ids(temp_db, sample_synthesis_setup):
    """6. Test that every finding traces to valid evidence_ids."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory overhead. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-trace-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Title", c1)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    for f in result.findings:
        assert len(f.evidence_ids) > 0
        assert "ev-trace-1" in f.evidence_ids


def test_finding_traceability_to_source_urls(temp_db, sample_synthesis_setup):
    """7. Test that every finding traces to valid source_urls."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory overhead. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-trace-2", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Title", c1)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    for f in result.findings:
        assert len(f.source_urls) > 0
        assert "https://arxiv.org/abs/2401.55555" in f.source_urls


def test_rejected_evidence_not_used_for_synthesis(temp_db, sample_synthesis_setup):
    """8. Test that evidence rejected during validation is excluded from synthesized findings."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c_valid = "Quantization of LLM transformer weights reduces memory overhead. " + ("Valid technical paper evaluation of deep learning. " * 8)
    c_rejected = "404 Not Found. Cookie policy JavaScript required."

    evidence_repo.create_evidence("ev-valid-sub", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Valid", c_valid)
    evidence_repo.create_evidence("ev-rej-sub", research.research_id, "https://example.com/404", "Bad", "Bad", c_rejected)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    all_linked_ev_ids = [ev_id for f in result.findings for ev_id in f.evidence_ids]
    assert "ev-valid-sub" in all_linked_ev_ids
    assert "ev-rej-sub" not in all_linked_ev_ids


def test_duplicate_evidence_does_not_duplicate_findings(temp_db, sample_synthesis_setup):
    """9. Test that candidate sentences matching an existing finding are merged into support_count."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces GPU memory requirements significantly. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    c2 = "Quantization of LLM transformer weights reduces GPU memory requirements significantly. " + ("Industry adoption metrics and production benchmark reports. " * 8)

    evidence_repo.create_evidence("ev-dup-f1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper 1", c1)
    evidence_repo.create_evidence("ev-dup-f2", research.research_id, "https://techcrunch.com/article", "TechCrunch", "Paper 2", c2)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    # The sentence appears in 2 distinct sources, so it merges into 1 finding with support_count = 2
    merged_finding = [f for f in result.findings if "quantization of llm transformer weights" in f.text.lower()][0]
    assert merged_finding.support_count == 2
    assert len(merged_finding.evidence_ids) == 2


def test_multiple_independent_sources_increase_support_and_confidence(temp_db, sample_synthesis_setup):
    """10. Test that support across distinct domains increases finding confidence."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory requirements significantly. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    c2 = "Quantization of LLM transformer weights reduces memory requirements significantly. " + ("Industry adoption metrics and production benchmark reports. " * 8)

    evidence_repo.create_evidence("ev-ind-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper 1", c1, confidence=0.85)
    evidence_repo.create_evidence("ev-ind-2", research.research_id, "https://techcrunch.com/report", "TechCrunch", "Paper 2", c2, confidence=0.85)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    finding = result.findings[0]
    assert finding.support_count == 2
    assert finding.confidence >= 0.90


def test_same_domain_sources_not_counted_as_independent(temp_db, sample_synthesis_setup):
    """11. Test that multiple pages on the same domain are tracked under 1 distinct domain."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory requirements. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    c2 = "Distillation of model weights improves inference throughput on GPUs. " + ("Further technical details on neural network optimization. " * 8)

    evidence_repo.create_evidence("ev-same-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper 1", c1)
    evidence_repo.create_evidence("ev-same-2", research.research_id, "https://arxiv.org/abs/2", "ArXiv", "Paper 2", c2)

    result = synthesize_research(
        research_id=research.research_id,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    assert result.source_diversity_count == 1
    assert result.distinct_domains == ["arxiv.org"]


def test_configurable_maximum_finding_count(temp_db, sample_synthesis_setup):
    """12. Test that max_findings limits the total findings returned."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory. Distillation speeds up inference latency. Model compression allows on-device deployment. Neural network pruning eliminates zero weights. Low rank adaptation enables fine tuning." + (" Further details. " * 8)

    evidence_repo.create_evidence("ev-max-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1)

    result = synthesize_research(
        research_id=research.research_id,
        max_findings=2,
        research_repo=SQLiteResearchRepository(temp_db),
        evidence_repo=evidence_repo,
        topic_repo=SQLiteTopicRepository(temp_db),
    )

    assert len(result.findings) <= 2


def test_deterministic_synthesis_results(temp_db, sample_synthesis_setup):
    """13. Test that running synthesis twice against unchanged database yields equivalent results."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization and distillation of large language models allows 8-bit model weight compression. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-det-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1)

    res1 = synthesize_research(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db))
    res2 = synthesize_research(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db))

    assert res1.overall_score == res2.overall_score
    assert len(res1.findings) == len(res2.findings)
    assert res1.findings[0].text == res2.findings[0].text


def test_limitation_generation(temp_db, sample_synthesis_setup):
    """14. Test human-readable limitation generation for single domain sourcing."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization of LLM transformer weights reduces memory footprint. " + ("Technical paper evaluation of deep learning architectures. " * 8)
    evidence_repo.create_evidence("ev-lim-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", c1)

    result = synthesize_research(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db))

    assert len(result.limitations) > 0
    assert any("Low source diversity" in lim for lim in result.limitations)


def test_basic_contradiction_conflict_detection(temp_db, sample_synthesis_setup):
    """15. Test detection of opposing numeric metric statements across evidence."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)

    c1 = "Quantization and distillation of large language models framework achieved accuracy 95% on benchmark evaluation tests. " + ("Unique detailed analysis from ArXiv paper on LLM quantization. " * 8)
    c2 = "Quantization and distillation of large language models framework achieved accuracy 70% on benchmark evaluation tests. " + ("Independent survey from TechCrunch on LLM model compression. " * 8)

    evidence_repo.create_evidence("ev-cnf-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper 1", c1)
    evidence_repo.create_evidence("ev-cnf-2", research.research_id, "https://techcrunch.com/news", "TechCrunch", "Article 2", c2)

    result = synthesize_research(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db))

    assert len(result.detected_conflicts) > 0
    assert any("accuracy" in c for c in result.detected_conflicts)


def test_existing_persistence_intact(temp_db, sample_synthesis_setup):
    """16. Test that running synthesis leaves all SQLite ResearchData and EvidenceData records intact."""
    topic, research = sample_synthesis_setup
    evidence_repo = SQLiteEvidenceRepository(temp_db)
    evidence_repo.create_evidence("ev-stay-1", research.research_id, "https://arxiv.org/abs/1", "ArXiv", "Paper", "Quantization of LLM transformer weights reduces memory footprint. " + ("Valid content " * 10))

    synthesize_research(research.research_id, research_repo=SQLiteResearchRepository(temp_db), evidence_repo=evidence_repo, topic_repo=SQLiteTopicRepository(temp_db))

    # Verify database records remain untouched
    db_res = SQLiteResearchRepository(temp_db).get_research(research.research_id)
    assert db_res is not None
    assert db_res.status == "completed"

    db_evs = SQLiteEvidenceRepository(temp_db).list_evidence_by_research(research.research_id)
    assert len(db_evs) == 1
    assert db_evs[0].evidence_id == "ev-stay-1"
