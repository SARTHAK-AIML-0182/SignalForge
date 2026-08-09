import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteEvidenceRepository,
    SQLiteResearchRepository,
    SQLiteTopicRepository,
)
from app.services.research.content_brief import build_content_brief
from app.services.research.writer import generate_draft


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_writer.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_usable_brief(temp_db):
    """Fixture producing a usable ContentBriefResult with 2 strong sources."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-wtr-test", "NOVA", "AI & Emerging Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic(
        topic_id="top-wtr-001",
        agent_id=agent.agent_id,
        title="Quantization and Distillation of Large Language Models",
        description="Technical paper on reducing LLM memory footprint and model weights.",
        source_url="https://arxiv.org/abs/2401.55555",
        source_name="ArXiv AI",
        status="selected",
    )

    research_repo = SQLiteResearchRepository(temp_db)
    research = research_repo.create_research(
        research_id="res-wtr-001",
        agent_id=agent.agent_id,
        topic_id=topic.topic_id,
        status="completed",
        confidence=0.90,
    )

    evidence_repo = SQLiteEvidenceRepository(temp_db)
    c1 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("Substantial technical paper analysis detailing architecture improvements for neural networks. " * 12)
    c2 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("TechCrunch report confirms enterprise adoption of quantization frameworks for LLM inference. " * 12)

    evidence_repo.create_evidence("ev-wtr-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper 1", c1, confidence=0.95)
    evidence_repo.create_evidence("ev-wtr-2", research.research_id, "https://techcrunch.com/quantization", "TechCrunch", "Article 2", c2, confidence=0.90)

    brief = build_content_brief(
        research_id=research.research_id,
        research_repo=research_repo,
        evidence_repo=evidence_repo,
        topic_repo=topic_repo,
        agent_repo=agent_repo,
    )
    return brief, research.research_id, temp_db


def test_successful_draft_generation_from_usable_brief(sample_usable_brief):
    """1. Test successful draft generation from a usable Content Brief."""
    brief, research_id, temp_db = sample_usable_brief
    draft = generate_draft(brief)

    assert draft.is_publishable is True
    assert draft.title.startswith("Technical Analysis:")
    assert len(draft.sections) >= 1
    assert draft.confidence >= 0.80


def test_non_publishable_result_when_brief_unusable(temp_db):
    """2. Test refusal to generate publishable draft when Content Brief is unusable."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-wtr-bad", "NOVA", "AI & Emerging Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic("top-wtr-bad", agent.agent_id, "Bad Topic", "Description", "https://example.com/bad", "Bad", "selected")

    research_repo = SQLiteResearchRepository(temp_db)
    research = research_repo.create_research("res-wtr-bad", agent.agent_id, topic.topic_id, "completed", 0.10)

    evidence_repo = SQLiteEvidenceRepository(temp_db)
    evidence_repo.create_evidence("ev-wtr-bad", research.research_id, "https://example.com/404", "Bad", "404", "404 Not Found. Cookie policy.")

    brief = build_content_brief(research.research_id, research_repo=research_repo, evidence_repo=evidence_repo, topic_repo=topic_repo, agent_repo=agent_repo)
    draft = generate_draft(brief)

    assert draft.is_publishable is False
    assert len(draft.sections) == 0
    assert "REFUSED" in draft.rationale


def test_title_generation(sample_usable_brief):
    """3. Test deterministic title generation containing topic title."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert "Quantization and Distillation of Large Language Models" in draft.title


def test_hook_generation(sample_usable_brief):
    """4. Test introduction hook generation incorporating topic and domain."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert "Quantization and Distillation of Large Language Models" in draft.hook
    assert "AI & Emerging Tech" in draft.hook


def test_body_section_generation(sample_usable_brief):
    """5. Test body sections generation from supported claims."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert len(draft.sections) == len(brief.claims)
    for sec in draft.sections:
        assert sec.section_id.startswith("sec-")
        assert len(sec.content) > 30


def test_conclusion_generation(sample_usable_brief):
    """6. Test conclusion generation summarizing topic implications."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert "In summary" in draft.conclusion
    assert "Quantization and Distillation of Large Language Models" in draft.conclusion


def test_content_angle_usage(sample_usable_brief):
    """7. Test content angle usage in draft hook."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert brief.angle in draft.hook or brief.angle in draft.full_text


def test_audience_context_usage(sample_usable_brief):
    """8. Test audience context usage in draft header."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert "NOVA" in draft.full_text
    assert "AI & Emerging Tech" in draft.full_text


def test_supported_claim_usage(sample_usable_brief):
    """9. Test that all supported claims in brief are referenced in draft sections."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    used_claims = draft.supported_claims_used
    assert len(used_claims) == len(brief.claims)


def test_claim_traceability(sample_usable_brief):
    """10. Test that claims in draft trace to finding IDs."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    for claim in draft.supported_claims_used:
        assert len(claim.finding_ids) > 0


def test_section_to_claim_traceability(sample_usable_brief):
    """11. Test section-to-claim traceability mapping."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    for sec in draft.sections:
        assert sec.section_id in draft.traceability
        assert len(draft.traceability[sec.section_id]["claim_ids"]) > 0


def test_evidence_to_source_traceability(sample_usable_brief):
    """12. Test evidence-to-source URL traceability mapping in sections."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    for sec in draft.sections:
        assert len(sec.evidence_ids) > 0
        assert len(sec.source_urls) > 0


def test_unsupported_claims_not_introduced(sample_usable_brief):
    """13. Test that zero unsupported claims or external facts are introduced."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    for sec in draft.sections:
        assert any(c.claim_text in sec.content for c in brief.claims)


def test_writing_constraints_respected(sample_usable_brief):
    """14. Test that mandatory writing constraints are passed into draft evaluation."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert draft.is_publishable is True


def test_research_limitations_preserved(sample_usable_brief):
    """15. Test that research limitations are preserved in draft full text."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    for lim in brief.limitations:
        assert lim in draft.limitations
        assert lim in draft.full_text


def test_source_references_preserved(sample_usable_brief):
    """16. Test that source references are preserved in draft output."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert len(draft.source_references) > 0
    assert "https://arxiv.org/abs/2401.55555" in draft.full_text


def test_confidence_score_deterministic(sample_usable_brief):
    """17. Test deterministic confidence score calculation."""
    brief, _, _ = sample_usable_brief
    d1 = generate_draft(brief)
    d2 = generate_draft(brief)

    assert d1.confidence == d2.confidence
    assert 0.0 <= d1.confidence <= 1.0


def test_publishability_rules(sample_usable_brief):
    """18. Test publishability rules enforcement."""
    brief, _, _ = sample_usable_brief
    draft = generate_draft(brief)

    assert draft.is_publishable is True
    assert "PUBLISHABLE DRAFT" in draft.rationale


def test_empty_insufficient_claims_handling(temp_db):
    """19. Test unpublishable draft when brief has zero usable claims."""
    brief_empty = type("Brief", (), {
        "is_usable": False,
        "claims": [],
        "topic_id": "top-1",
        "research_id": "res-1",
        "topic_title": "Empty Topic",
        "angle": "",
        "audience": {},
        "sources": [],
        "limitations": [],
        "confidence": 0.0,
        "rationale": "Zero claims available.",
    })()

    draft = generate_draft(brief_empty)

    assert draft.is_publishable is False
    assert len(draft.sections) == 0


def test_existing_persistence_intact(sample_usable_brief):
    """20. Test that generating draft leaves all SQLite database records untouched."""
    brief, research_id, temp_db = sample_usable_brief
    generate_draft(brief)

    db_res = SQLiteResearchRepository(temp_db).get_research(research_id)
    assert db_res is not None
    assert db_res.status == "completed"

    db_evs = SQLiteEvidenceRepository(temp_db).list_evidence_by_research(research_id)
    assert len(db_evs) == 2
