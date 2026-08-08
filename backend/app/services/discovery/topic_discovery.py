import logging
import secrets
from typing import List, Optional, Set

import httpx

from app.repositories import BaseTopicRepository, TopicData, get_topic_repository
from app.services.discovery.feed_parser import parse_feed_xml
from app.services.discovery.sources import DEFAULT_FEEDS, FeedSource

logger = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SignalForge/1.0"
}


def fetch_feed(client: httpx.Client, feed_url: str) -> Optional[str]:
    """Fetch raw feed XML from network with timeout and error handling."""
    try:
        response = client.get(feed_url, follow_redirects=True)
        if response.status_code == 200:
            return response.text
        logger.warning(f"Failed to fetch feed {feed_url}: status {response.status_code}")
        return None
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning(f"Error fetching feed {feed_url}: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error fetching feed {feed_url}: {exc}")
        return None


def discover_topics(
    agent_id: str,
    repo: Optional[BaseTopicRepository] = None,
    feeds: Optional[List[FeedSource]] = None,
    http_client: Optional[httpx.Client] = None,
    timeout: float = 10.0,
) -> List[TopicData]:
    """
    Independently discover current AI and technology topics from live public RSS/Atom feeds.
    Normalizes feed entries, prevents duplicates, and persists new topics into SQLite.
    """
    if repo is None:
        repo = get_topic_repository()

    feed_list = feeds if feeds is not None else DEFAULT_FEEDS

    # Pre-populate deduplication set with existing agent topics
    existing_topics = repo.list_topics_by_agent(agent_id)
    seen_urls: Set[str] = {t.source_url for t in existing_topics if t.source_url}
    seen_titles: Set[str] = {t.title.lower().strip() for t in existing_topics if t.title}

    new_discovered_topics: List[TopicData] = []

    # Use provided client or instantiate a new httpx.Client with standard browser headers
    client_provided = http_client is not None
    client = http_client if http_client is not None else httpx.Client(timeout=timeout, headers=DEFAULT_HEADERS)

    try:
        for feed in feed_list:
            feed_name = feed.get("name", "Unknown Source")
            feed_url = feed.get("url", "")
            if not feed_url:
                continue

            raw_xml = fetch_feed(client, feed_url)
            if not raw_xml:
                continue

            parsed_items = parse_feed_xml(raw_xml)
            for item in parsed_items:
                normalized_url = item.source_url.strip()
                normalized_title = item.title.lower().strip()

                # Deduplication check (URL or Title already processed or stored)
                if normalized_url in seen_urls or normalized_title in seen_titles:
                    continue

                seen_urls.add(normalized_url)
                seen_titles.add(normalized_title)

                topic_id = f"topic-{secrets.token_hex(16)}"
                created_topic = repo.create_topic(
                    topic_id=topic_id,
                    agent_id=agent_id,
                    title=item.title,
                    description=item.description,
                    source_url=item.source_url,
                    source_name=feed_name,
                    editorial_score=0.0,
                    status="discovered",
                )
                new_discovered_topics.append(created_topic)
    finally:
        if not client_provided:
            client.close()

    return new_discovered_topics
