"""Live topic discovery service package."""

from app.services.discovery.feed_parser import ParsedFeedItem, parse_feed_xml
from app.services.discovery.sources import DEFAULT_FEEDS, FeedSource
from app.services.discovery.topic_discovery import discover_topics, fetch_feed

__all__ = [
    "DEFAULT_FEEDS",
    "FeedSource",
    "ParsedFeedItem",
    "parse_feed_xml",
    "discover_topics",
    "fetch_feed",
]
