from typing import List
from urllib.parse import urlparse

from app.repositories import EvidenceData

REPUTABLE_DOMAINS = {
    "arxiv.org",
    "huggingface.co",
    "techcrunch.com",
    "github.com",
    "nature.com",
    "mit.edu",
    "venturebeat.com",
    "openai.com",
    "anthropic.com",
    "deepmind.com",
    "technologyreview.com",
    "biorxiv.org",
    "medrxiv.org",
}


def score_evidence_confidence(
    source_url: str,
    is_primary: bool,
    content: str,
    title: str,
) -> float:
    """
    Calculate deterministic confidence score for an evidence source (0.0 to 1.0).
    Evaluates primary source status, domain reputation, and content length.
    """
    domain = urlparse(source_url).netloc.lower().replace("www.", "")

    base_score = 0.85 if is_primary else 0.65

    # Bonus for recognized technical/publication domains
    if any(rep_domain in domain for rep_domain in REPUTABLE_DOMAINS):
        base_score += 0.10

    # Content length evaluation
    content_len = len(content.strip()) if content else 0
    if content_len >= 300:
        base_score += 0.10
    elif content_len < 50:
        base_score -= 0.30

    return max(0.10, min(0.98, round(base_score, 2)))


def compute_research_confidence(evidence_list: List[EvidenceData]) -> float:
    """
    Calculate overall research confidence score (0.0 to 1.0) based on collected evidence.
    Evaluates quantity, primary source presence, and individual evidence confidence.
    """
    if not evidence_list:
        return 0.0

    max_ev_confidence = max(e.confidence for e in evidence_list)
    multi_source_bonus = 0.08 * (len(evidence_list) - 1)

    total = max_ev_confidence + multi_source_bonus
    return max(0.0, min(0.98, round(total, 2)))
