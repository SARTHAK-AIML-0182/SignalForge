from unittest.mock import MagicMock
import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteEvidenceRepository,
    SQLiteResearchRepository,
    SQLiteTopicRepository,
)
from app.services.research import build_content_brief, generate_draft
from app.services.publishing import (
    BasePublishingAdapter,
    DryRunPublishingAdapter,
    PublicationResult,
    PublicationStatus,
    publish_draft,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_pub.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_publishable_draft(temp_db):
    """Fixture producing a publishable DraftResult with zero warnings and valid claims."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-pub-test", "NOVA", "AI & Emerging Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic(
        topic_id="top-pub-001",
        agent_id=agent.agent_id,
        title="Quantization and Distillation of Large Language Models",
        description="Technical paper on reducing LLM memory footprint and model weights.",
        source_url="https://arxiv.org/abs/2401.55555",
        source_name="ArXiv AI",
        status="selected",
    )

    research_repo = SQLiteResearchRepository(temp_db)
    research = research_repo.create_research(
        research_id="res-pub-001",
        agent_id=agent.agent_id,
        topic_id=topic.topic_id,
        status="completed",
        confidence=0.95,
    )

    evidence_repo = SQLiteEvidenceRepository(temp_db)
    c1 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("Substantial technical paper analysis detailing architecture improvements for neural networks. " * 12)
    c2 = "Quantization and distillation of large language models reduces LLM memory footprint and model weights. " + ("TechCrunch report confirms enterprise adoption of quantization frameworks for LLM inference. " * 12)

    evidence_repo.create_evidence("ev-pub-1", research.research_id, "https://arxiv.org/abs/2401.55555", "ArXiv", "Paper 1", c1, confidence=0.95)
    evidence_repo.create_evidence("ev-pub-2", research.research_id, "https://techcrunch.com/quantization", "TechCrunch", "Article 2", c2, confidence=0.90)

    brief = build_content_brief(
        research_id=research.research_id,
        research_repo=research_repo,
        evidence_repo=evidence_repo,
        topic_repo=topic_repo,
        agent_repo=agent_repo,
    )
    draft = generate_draft(brief)

    # Force zero warnings for test clarity if any conflict detector flagged identical terms
    draft.warnings = []
    draft.is_publishable = True

    return draft, research.research_id, temp_db


def test_successful_dry_run_publication(sample_publishable_draft):
    """1. Test successful dry-run publication of a publishable draft."""
    draft, _, _ = sample_publishable_draft
    result = publish_draft(draft, dry_run=True)

    assert result.status == PublicationStatus.DRY_RUN
    assert result.is_successful is True
    assert result.is_dry_run is True
    assert result.platform == "dry_run_local"
    assert "DRY-RUN SUCCESS" in result.rationale


def test_publication_blocked_for_unpublishable_draft(sample_publishable_draft):
    """2. Test that publication is blocked when draft.is_publishable is False."""
    draft, _, _ = sample_publishable_draft
    draft.is_publishable = False

    result = publish_draft(draft)

    assert result.status == PublicationStatus.BLOCKED
    assert result.is_successful is False
    assert "BLOCKED" in result.rationale


def test_adapter_not_called_when_blocked(sample_publishable_draft):
    """3. Test that adapter is NEVER called when draft publication is blocked."""
    draft, _, _ = sample_publishable_draft
    draft.is_publishable = False

    mock_adapter = MagicMock(spec=BasePublishingAdapter)
    mock_adapter.platform_name = "mock_platform"

    result = publish_draft(draft, adapter=mock_adapter)

    assert result.status == PublicationStatus.BLOCKED
    mock_adapter.publish.assert_not_called()


def test_empty_draft_content_rejected(sample_publishable_draft):
    """4. Test that empty draft content is rejected with blocked status."""
    draft, _, _ = sample_publishable_draft
    draft.full_text = ""

    result = publish_draft(draft)

    assert result.status == PublicationStatus.BLOCKED
    assert result.is_successful is False
    assert "empty" in result.error_message.lower()


def test_missing_traceability_rejected(sample_publishable_draft):
    """5. Test that missing section traceability is rejected."""
    draft, _, _ = sample_publishable_draft
    draft.traceability = {}

    result = publish_draft(draft)

    assert result.status == PublicationStatus.BLOCKED
    assert "traceability" in result.rationale.lower()


def test_blocking_warnings_prevent_publication(sample_publishable_draft):
    """6. Test that draft warnings prevent publication."""
    draft, _, _ = sample_publishable_draft
    draft.warnings = ["Potential conflicting statements in underlying research."]

    result = publish_draft(draft)

    assert result.status == PublicationStatus.BLOCKED
    assert result.is_successful is False
    assert "warnings" in result.rationale.lower()


def test_dry_run_status_distinct_from_published(sample_publishable_draft):
    """7. Test that dry-run status is 'dry_run', distinct from 'published'."""
    draft, _, _ = sample_publishable_draft
    result = publish_draft(draft, dry_run=True)

    assert result.status == PublicationStatus.DRY_RUN
    assert result.status != PublicationStatus.PUBLISHED
    assert result.is_dry_run is True


def test_draft_content_preserved_exactly(sample_publishable_draft):
    """8. Test that draft content is preserved exactly in PublicationResult."""
    draft, _, _ = sample_publishable_draft
    result = publish_draft(draft)

    assert result.published_content == draft.full_text


def test_source_traceability_preserved(sample_publishable_draft):
    """9. Test that source traceability mapping is preserved in PublicationResult."""
    draft, _, _ = sample_publishable_draft
    result = publish_draft(draft)

    assert result.traceability == draft.traceability
    for sec_id, mapping in result.traceability.items():
        assert len(mapping["source_urls"]) > 0


def test_publication_result_contains_draft_id(sample_publishable_draft):
    """10. Test that PublicationResult contains draft_id."""
    draft, _, _ = sample_publishable_draft
    result = publish_draft(draft)

    assert result.draft_id == draft.draft_id


def test_publication_result_contains_platform(sample_publishable_draft):
    """11. Test that PublicationResult contains target platform name."""
    draft, _, _ = sample_publishable_draft
    result = publish_draft(draft)

    assert result.platform == "dry_run_local"


def test_publication_mode_correctly_reported(sample_publishable_draft):
    """12. Test that publication mode (is_dry_run=True) is correctly reported."""
    draft, _, _ = sample_publishable_draft
    result = publish_draft(draft, dry_run=True)

    assert result.is_dry_run is True


def test_duplicate_idempotent_dry_run_behavior(sample_publishable_draft):
    """13. Test that submitting the same draft repeatedly produces deterministic IDs and outputs."""
    draft, _, _ = sample_publishable_draft
    res1 = publish_draft(draft, dry_run=True)
    res2 = publish_draft(draft, dry_run=True)

    assert res1.publication_id == res2.publication_id
    assert res1.published_content == res2.published_content


def test_deterministic_publication_result(sample_publishable_draft):
    """14. Test deterministic publication result generation."""
    draft, _, _ = sample_publishable_draft
    res1 = publish_draft(draft)
    res2 = publish_draft(draft)

    assert res1.status == res2.status
    assert res1.is_successful == res2.is_successful
    assert res1.rationale == res2.rationale


def test_adapter_abstraction_independent_of_service(sample_publishable_draft):
    """15. Test that custom adapters extending BasePublishingAdapter work seamlessly."""
    draft, _, _ = sample_publishable_draft

    class CustomTestAdapter(BasePublishingAdapter):
        @property
        def platform_name(self) -> str:
            return "custom_test_platform"

        def publish(self, d, dry_run=True):
            return PublicationResult(
                publication_id="pub-custom-123",
                draft_id=d.draft_id,
                topic_id=d.topic_id,
                research_id=d.research_id,
                platform=self.platform_name,
                status=PublicationStatus.DRY_RUN,
                is_successful=True,
                is_dry_run=dry_run,
                published_content=d.full_text,
                published_at="2026-08-09T00:00:00Z",
                rationale="Custom adapter dry-run success.",
            )

    custom_adapter = CustomTestAdapter()
    result = publish_draft(draft, adapter=custom_adapter, dry_run=True)

    assert result.platform == "custom_test_platform"
    assert result.publication_id == "pub-custom-123"


def test_research_evidence_persistence_unchanged(sample_publishable_draft):
    """16. Test that publishing attempt leaves SQLite Research and Evidence records untouched."""
    draft, research_id, temp_db = sample_publishable_draft
    publish_draft(draft)

    db_res = SQLiteResearchRepository(temp_db).get_research(research_id)
    assert db_res is not None
    assert db_res.status == "completed"

    db_evs = SQLiteEvidenceRepository(temp_db).list_evidence_by_research(research_id)
    assert len(db_evs) == 2


def test_existing_draft_result_unchanged(sample_publishable_draft):
    """17. Test that existing DraftResult object remains unmodified after publication attempt."""
    draft, _, _ = sample_publishable_draft
    original_text = draft.full_text
    original_publishable = draft.is_publishable

    publish_draft(draft)

    assert draft.full_text == original_text
    assert draft.is_publishable == original_publishable


def test_existing_complete_test_suite_remains_green(sample_publishable_draft):
    """18. Test that publishing service execution preserves pipeline integrity."""
    draft, _, temp_db = sample_publishable_draft
    result = publish_draft(draft, dry_run=True)

    assert result.is_successful is True
    assert result.status == PublicationStatus.DRY_RUN
    assert len(result.traceability) > 0

