"""Centralized configuration for live RSS and Atom discovery sources."""

from typing import List, TypedDict


class FeedSource(TypedDict):
    name: str
    url: str
    category: str


DEFAULT_FEEDS: List[FeedSource] = [
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "open_source_ai",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "ai_news",
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "category": "ai_analysis",
    },
    {
        "name": "ArXiv AI Research",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "category": "ai_research",
    },
    {
        "name": "ArXiv NLP & Language Models",
        "url": "https://rss.arxiv.org/rss/cs.CL",
        "category": "ai_research",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://feed.venturebeat.com/category/ai",
        "category": "ai_news",
    },
]
