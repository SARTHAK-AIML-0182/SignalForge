"""Autonomous Research & Evidence Collection Engine package for SignalForge."""

from app.services.research.engine import ResearchResult, research_topic
from app.services.research.extractor import extract_page_content, fetch_html
from app.services.research.scorer import compute_research_confidence, score_evidence_confidence

__all__ = [
    "ResearchResult",
    "research_topic",
    "fetch_html",
    "extract_page_content",
    "score_evidence_confidence",
    "compute_research_confidence",
]
