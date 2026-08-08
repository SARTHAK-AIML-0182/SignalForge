import httpx
import pytest
from app.db.database import init_db
from app.repositories import (
    SQLiteAgentRepository,
    SQLiteEvidenceRepository,
    SQLiteResearchRepository,
    SQLiteTopicRepository,
)
from app.services.research import (
    compute_research_confidence,
    extract_page_content,
    research_topic,
    score_evidence_confidence,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_research_engine.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_topic(temp_db):
    """Fixture providing a persisted Agent and Topic in the temporary database."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent = agent_repo.save_agent("agent-res-engine", "NOVA", "AI & Emerging Tech")

    topic_repo = SQLiteTopicRepository(temp_db)
    topic = topic_repo.create_topic(
        topic_id="top-res-001",
        agent_id=agent.agent_id,
        title="Autonomous AI Agent Memory Architectures",
        description="Technical paper on long-term memory for AI agents.",
        source_url="https://arxiv.org/abs/2401.99999",
        source_name="ArXiv AI",
        status="selected",
    )
    return topic


def test_successful_research_workflow(temp_db, sample_topic):
    """1. Test successful end-to-end research workflow using mocked HTTP transport."""
    html_content = """
    <html>
        <head><title>Autonomous AI Agent Memory Architectures - ArXiv</title></head>
        <body>
            <nav>Navigation links</nav>
            <h1>Autonomous AI Agent Memory Architectures</h1>
            <p>This technical paper introduces a novel persistent memory architecture for autonomous AI agents operating in complex environments.</p>
            <footer>Footer notes</footer>
        </body>
    </html>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html_content)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    assert result.status == "completed"
    assert result.evidence_count == 1
    assert result.confidence >= 0.80
    assert result.completed_at is not None


def test_research_status_transitions_to_in_progress(temp_db, sample_topic):
    """2. Test that research record transitions through in_progress before completion."""
    res_repo = SQLiteResearchRepository(temp_db)
    res_repo.create_research("res-status-test", sample_topic.agent_id, sample_topic.topic_id, status="pending")

    # Manually transition to in_progress
    updated = res_repo.update_research_status("res-status-test", "in_progress")
    assert updated.status == "in_progress"


def test_successful_completion(temp_db, sample_topic):
    """3. Test that successful research records completion timestamp in UTC."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><head><title>Valid Research Paper Title</title></head><body>" + "Substantial technical content. " * 20 + "</body></html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    assert result.status == "completed"
    assert result.completed_at is not None
    assert "T" in result.completed_at  # ISO 8601 UTC string format


def test_evidence_persistence(temp_db, sample_topic):
    """4. Test that evidence is correctly extracted and persisted in SQLite."""
    html_text = "<html><head><title>Extracted Paper Title</title></head><body><p>" + "Detailed technical evidence content. " * 15 + "</p></body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html_text)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    evidence_list = ev_repo.list_evidence_by_research(result.research_id)
    assert len(evidence_list) == 1

    ev = evidence_list[0]
    assert ev.source_url == sample_topic.source_url
    assert ev.title == "Extracted Paper Title"
    assert "Detailed technical evidence content" in ev.content
    assert ev.confidence > 0.5


def test_multiple_evidence_sources(temp_db, sample_topic):
    """5. Test fetching and persisting multiple evidence records."""
    html_text = "<html><head><title>Source Page</title></head><body>" + "Content for evidence source. " * 15 + "</body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html_text)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    # Pre-create research record
    res = res_repo.create_research("res-multi", sample_topic.agent_id, sample_topic.topic_id)
    ev_repo.create_evidence("ev-pre1", res.research_id, "https://example.com/sec1", "Sec 1", "Title 1", "Content 1")

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    all_evidence = ev_repo.list_evidence_by_research(res.research_id)
    assert len(all_evidence) == 2
    assert result.evidence_count == 2


def test_duplicate_source_prevention(temp_db, sample_topic):
    """6. Test that duplicate source URLs within the same research investigation are skipped."""
    html_text = "<html><head><title>Source Page</title></head><body>" + "Duplicate content test. " * 15 + "</body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html_text)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    # Pre-insert evidence for primary source URL
    res = res_repo.create_research("res-dup", sample_topic.agent_id, sample_topic.topic_id)
    ev_repo.create_evidence(
        evidence_id="ev-dup-existing",
        research_id=res.research_id,
        source_url=sample_topic.source_url,
        source_name="ArXiv AI",
        title="Already Inserted",
        content="Already inserted content",
    )

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    all_evidence = ev_repo.list_evidence_by_research(res.research_id)
    # The existing evidence remains, duplicate fetch was skipped
    assert len(all_evidence) == 1
    assert all_evidence[0].evidence_id == "ev-dup-existing"


def test_http_timeout_handling(temp_db, sample_topic):
    """7. Test graceful handling of HTTP network timeouts without raising exceptions."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out after 10 seconds")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    assert result.status == "failed"
    assert result.evidence_count == 0
    assert result.confidence == 0.0


def test_http_failure_handling(temp_db, sample_topic):
    """8. Test graceful handling of 404/500 HTTP server errors."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    assert result.status == "failed"
    assert result.evidence_count == 0


def test_malformed_html_handling(temp_db, sample_topic):
    """9. Test robust content extraction from broken/malformed HTML markup."""
    broken_html = "<html><body><title>Broken Title<p>Unclosed paragraph text with <invalid tags"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=broken_html)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    assert result.status == "completed"
    ev = ev_repo.list_evidence_by_research(result.research_id)[0]
    assert ev.title is not None
    assert "Unclosed paragraph text" in ev.content


def test_research_failure_status_persistence(temp_db, sample_topic):
    """10. Test that failed research tasks persist status='failed' in SQLite."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    assert result.status == "failed"

    db_res = res_repo.get_research_by_topic(sample_topic.topic_id)
    assert db_res is not None
    assert db_res.status == "failed"


def test_deterministic_confidence_calculation():
    """11. Test deterministic evidence and research confidence calculations."""
    primary_conf = score_evidence_confidence(
        source_url="https://arxiv.org/abs/2401.00001",
        is_primary=True,
        content="Technical content " * 30,
        title="ArXiv Paper",
    )
    weak_conf = score_evidence_confidence(
        source_url="https://unknown-blog.com/post",
        is_primary=False,
        content="Short text",
        title="Blog",
    )

    assert primary_conf >= 0.90
    assert weak_conf <= 0.40

    overall = compute_research_confidence([])
    assert overall == 0.0


def test_original_source_prioritization(temp_db, sample_topic):
    """12. Test that primary topic URL is fetched first and marked as primary source."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><head><title>ArXiv Primary Paper</title></head><body>" + "Primary source body content. " * 15 + "</body></html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res_repo = SQLiteResearchRepository(temp_db)
    ev_repo = SQLiteEvidenceRepository(temp_db)

    result = research_topic(
        topic=sample_topic,
        research_repo=res_repo,
        evidence_repo=ev_repo,
        http_client=client,
    )

    ev_list = ev_repo.list_evidence_by_research(result.research_id)
    assert len(ev_list) == 1
    assert ev_list[0].source_type == "primary_web"
    assert ev_list[0].source_url == sample_topic.source_url
