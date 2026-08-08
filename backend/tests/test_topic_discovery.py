from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.db.database import init_db
from app.repositories import SQLiteAgentRepository, SQLiteTopicRepository
from app.services.discovery.feed_parser import parse_feed_xml
from app.services.discovery.topic_discovery import discover_topics, fetch_feed

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tech News</title>
    <link>https://example.com</link>
    <description>AI News</description>
    <item>
      <title>Breakthrough in Autonomous AI Agents</title>
      <link>https://example.com/ai-agent-breakthrough</link>
      <description>&lt;p&gt;New multi-agent framework announced.&lt;/p&gt;</description>
      <pubDate>Fri, 08 Aug 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Open-Source LLM Achieves SOTA</title>
      <link>https://example.com/open-source-sota</link>
      <description>Benchmarks show high efficiency.</description>
      <pubDate>Fri, 08 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Open AI Research Feed</title>
  <entry>
    <title>Fast Inference for Vision Language Models</title>
    <link href="https://huggingface.co/blog/vlm-inference" rel="alternate"/>
    <summary>Optimizing VLM inference speed with FlashAttention.</summary>
    <updated>2026-08-08T14:00:00Z</updated>
  </entry>
</feed>
"""

MALFORMED_XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Broken Feed
    <item>
      <title>Unclosed tag
      <link>https://example.com/broken
"""


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_discovery.db"
    init_db(db_file)
    return db_file


def test_rss_feed_parsing():
    """Test successful parsing of RSS 2.0 feeds."""
    items = parse_feed_xml(SAMPLE_RSS)
    assert len(items) == 2

    item1 = items[0]
    assert item1.title == "Breakthrough in Autonomous AI Agents"
    assert item1.source_url == "https://example.com/ai-agent-breakthrough"
    assert "multi-agent framework" in item1.description

    item2 = items[1]
    assert item2.title == "Open-Source LLM Achieves SOTA"
    assert item2.source_url == "https://example.com/open-source-sota"


def test_atom_feed_parsing():
    """Test successful parsing of Atom feeds."""
    items = parse_feed_xml(SAMPLE_ATOM)
    assert len(items) == 1

    entry = items[0]
    assert entry.title == "Fast Inference for Vision Language Models"
    assert entry.source_url == "https://huggingface.co/blog/vlm-inference"
    assert "FlashAttention" in entry.description


def test_malformed_feed_handling():
    """Test that malformed XML feeds do not crash parsing and return empty list."""
    items = parse_feed_xml(MALFORMED_XML)
    assert items == []


def test_unavailable_feed_handling():
    """Test graceful handling of HTTP errors and timeouts when fetching feeds."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectTimeout("Connection timed out")

    raw_xml = fetch_feed(mock_client, "https://unavailable-feed.com/rss")
    assert raw_xml is None

    mock_client.get.side_effect = None
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_client.get.return_value = mock_response

    raw_xml_500 = fetch_feed(mock_client, "https://unavailable-feed.com/500")
    assert raw_xml_500 is None


def test_discover_topics_mocked(temp_db):
    """Test full topic discovery flow with mocked HTTP responses and persistence."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent_repo.save_agent("agent-disc-01", "NOVA", "AI Tech")
    topic_repo = SQLiteTopicRepository(temp_db)

    # Mock HTTP transport
    def handler(request: httpx.Request) -> httpx.Response:
        if "rss" in str(request.url):
            return httpx.Response(200, text=SAMPLE_RSS)
        elif "atom" in str(request.url):
            return httpx.Response(200, text=SAMPLE_ATOM)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    mock_client = httpx.Client(transport=transport)

    test_feeds = [
        {"name": "RSS Source", "url": "https://test.com/rss", "category": "ai"},
        {"name": "Atom Source", "url": "https://test.com/atom", "category": "ai"},
    ]

    discovered = discover_topics(
        agent_id="agent-disc-01",
        repo=topic_repo,
        feeds=test_feeds,
        http_client=mock_client
    )

    assert len(discovered) == 3

    # Check persistence in SQLite
    stored_topics = topic_repo.list_topics_by_agent("agent-disc-01")
    assert len(stored_topics) == 3
    
    titles = [t.title for t in stored_topics]
    assert "Breakthrough in Autonomous AI Agents" in titles
    assert "Open-Source LLM Achieves SOTA" in titles
    assert "Fast Inference for Vision Language Models" in titles

    for topic in stored_topics:
        assert topic.status == "discovered"
        assert topic.discovered_at is not None
        assert topic.source_name in ("RSS Source", "Atom Source")


def test_duplicate_detection(temp_db):
    """Test that duplicate URLs or titles are not saved multiple times."""
    agent_repo = SQLiteAgentRepository(temp_db)
    agent_repo.save_agent("agent-dedup", "Deduper", "AI")
    topic_repo = SQLiteTopicRepository(temp_db)

    # Pre-populate repository with an existing topic
    topic_repo.create_topic(
        topic_id="existing-01",
        agent_id="agent-dedup",
        title="Breakthrough in Autonomous AI Agents",
        source_url="https://example.com/ai-agent-breakthrough",
        source_name="Existing Feed"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SAMPLE_RSS)

    transport = httpx.MockTransport(handler)
    mock_client = httpx.Client(transport=transport)

    test_feeds = [
        {"name": "Duplicate Feed", "url": "https://test.com/rss", "category": "ai"},
    ]

    discovered = discover_topics(
        agent_id="agent-dedup",
        repo=topic_repo,
        feeds=test_feeds,
        http_client=mock_client
    )

    # Out of 2 items in SAMPLE_RSS, 1 URL/title is already in DB, so only 1 new topic should be discovered
    assert len(discovered) == 1
    assert discovered[0].title == "Open-Source LLM Achieves SOTA"

    total_topics = topic_repo.list_topics_by_agent("agent-dedup")
    assert len(total_topics) == 2
