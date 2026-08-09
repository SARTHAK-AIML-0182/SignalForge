import html
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from app.repositories import (
    BaseEvidenceRepository,
    BaseResearchRepository,
    BaseTopicRepository,
    EvidenceData,
    get_evidence_repository,
    get_research_repository,
    get_topic_repository,
)

STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "up", "about", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "it", "its", "this", "that", "these", "those", "how", "why", "what",
    "when", "where", "who", "which", "says", "new", "via", "http", "https", "com",
    "org", "net"
}

TIER_1_DOMAINS: Set[str] = {
    "arxiv.org", "biorxiv.org", "medrxiv.org", "nature.com", "mit.edu",
    "openai.com", "anthropic.com", "deepmind.com"
}

TIER_2_DOMAINS: Set[str] = {
    "huggingface.co", "techcrunch.com", "github.com", "venturebeat.com",
    "technologyreview.com"
}

SPAM_PATTERNS: Set[str] = {
    "clickbait", "gossip", "free-download", "promotes", "casino", "betting"
}


def tokenize(text: str) -> Set[str]:
    """Tokenize text into lowercase alphanumeric words, stripping stop words."""
    words = re.findall(r"\b[a-z0-9_]+\b", text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 1}


@dataclass
class EvidenceValidationItem:
    evidence_id: str
    is_valid: bool
    score: float
    signals: Dict[str, float]
    rejection_reasons: List[str]


@dataclass
class ResearchValidationResult:
    research_id: str
    topic_id: str
    is_usable: bool
    overall_score: float
    quality_classification: str  # "strong", "acceptable", "insufficient", "unusable"
    needs_additional_research: bool
    evidence_items: List[EvidenceValidationItem]
    usable_evidence_count: int
    rejected_evidence_count: int
    rationale: str


def score_source_quality(source_url: str, source_name: str) -> float:
    """Evaluate source domain reputation and quality (0.0 to 1.0)."""
    domain = urlparse(source_url).netloc.lower().replace("www.", "")

    if any(spam in domain for spam in SPAM_PATTERNS):
        return 0.20

    if any(t1 in domain for t1 in TIER_1_DOMAINS):
        return 1.0
    elif any(t2 in domain for t2 in TIER_2_DOMAINS):
        return 0.85
    elif domain:
        return 0.50
    else:
        return 0.30


def score_content_quality(content: str) -> float:
    """Evaluate content length, information density, and boilerplate (0.0 to 1.0)."""
    cleaned = content.strip()
    if not cleaned:
        return 0.0

    boilerplate_indicators = [
        "404 not found", "javascript required", "cookie policy",
        "sign in to continue", "all rights reserved navigation",
        "turn off adblocker"
    ]
    low_content_matches = sum(1 for bp in boilerplate_indicators if bp in cleaned.lower())
    if low_content_matches >= 2 or len(cleaned) < 80:
        return 0.15

    content_len = len(cleaned)
    if content_len >= 800:
        return 0.95
    elif content_len >= 250:
        return 0.75
    else:
        return 0.45


def score_topic_relevance(topic_title: str, topic_desc: Optional[str], content: str) -> float:
    """Evaluate token overlap between topic information and evidence content (0.0 to 1.0)."""
    topic_text = f"{topic_title} {topic_desc or ''}"
    topic_tokens = tokenize(topic_text)
    content_tokens = tokenize(content)

    if not topic_tokens or not content_tokens:
        return 0.30

    intersection = topic_tokens.intersection(content_tokens)
    ratio = len(intersection) / len(topic_tokens)
    return max(0.10, min(1.0, round(ratio * 1.4, 2)))


def detect_redundancy(evidence_list: List[EvidenceData]) -> Dict[str, bool]:
    """Detect duplicate or near-duplicate evidence items in a research investigation."""
    redundant_map: Dict[str, bool] = {e.evidence_id: False for e in evidence_list}

    for i in range(len(evidence_list)):
        e_i = evidence_list[i]
        tokens_i = tokenize(e_i.content)

        for j in range(i + 1, len(evidence_list)):
            e_j = evidence_list[j]
            if redundant_map[e_j.evidence_id]:
                continue

            # Exact URL duplicate check
            if e_i.source_url.strip().lower() == e_j.source_url.strip().lower():
                redundant_map[e_j.evidence_id] = True
                continue

            # Text content Jaccard similarity
            tokens_j = tokenize(e_j.content)
            if tokens_i and tokens_j:
                union = tokens_i.union(tokens_j)
                intersection = tokens_i.intersection(tokens_j)
                similarity = len(intersection) / len(union) if union else 0.0
                if similarity >= 0.60:
                    redundant_map[e_j.evidence_id] = True

    return redundant_map


def score_source_diversity(usable_evidence: List[EvidenceData]) -> float:
    """Evaluate source domain diversity among usable evidence items (0.0 to 1.0)."""
    if not usable_evidence:
        return 0.0

    domains = {
        urlparse(e.source_url).netloc.lower().replace("www.", "")
        for e in usable_evidence
        if e.source_url
    }

    if len(domains) >= 3:
        return 1.0
    elif len(domains) == 2:
        return 0.80
    elif len(domains) == 1:
        return 0.50
    else:
        return 0.0


def score_evidence_completeness(usable_evidence: List[EvidenceData]) -> float:
    """Evaluate total supporting content volume across usable evidence items (0.0 to 1.0)."""
    if not usable_evidence:
        return 0.0

    total_chars = sum(len(e.content.strip()) for e in usable_evidence if e.content)

    if total_chars >= 1500:
        return 1.0
    elif total_chars >= 300:
        return 0.75
    elif total_chars > 0:
        return 0.35
    else:
        return 0.0


def validate_research(
    research_id: str,
    research_repo: Optional[BaseResearchRepository] = None,
    evidence_repo: Optional[BaseEvidenceRepository] = None,
    topic_repo: Optional[BaseTopicRepository] = None,
    threshold: float = 0.65,
) -> ResearchValidationResult:
    """
    Validate research quality and evidence usefulness for a given research investigation.
    Returns a ResearchValidationResult explaining usability, quality classification, and individual item status.
    No evidence records are deleted from SQLite.
    """
    if research_repo is None:
        research_repo = get_research_repository()
    if evidence_repo is None:
        evidence_repo = get_evidence_repository()
    if topic_repo is None:
        topic_repo = get_topic_repository()

    research = research_repo.get_research(research_id)
    if not research:
        return ResearchValidationResult(
            research_id=research_id,
            topic_id="",
            is_usable=False,
            overall_score=0.0,
            quality_classification="unusable",
            needs_additional_research=True,
            evidence_items=[],
            usable_evidence_count=0,
            rejected_evidence_count=0,
            rationale=f"UNUSABLE: Research ID '{research_id}' not found.",
        )

    topic = topic_repo.get_topic(research.topic_id)
    topic_title = topic.title if topic else ""
    topic_desc = topic.description if topic else ""

    all_evidence = evidence_repo.list_evidence_by_research(research_id)
    redundancy_map = detect_redundancy(all_evidence)

    evidence_validation_items: List[EvidenceValidationItem] = []
    usable_evidence_list: List[EvidenceData] = []

    for ev in all_evidence:
        src_q = score_source_quality(ev.source_url, ev.source_name)
        cnt_q = score_content_quality(ev.content)
        rel_q = score_topic_relevance(topic_title, topic_desc, ev.content)
        is_red = redundancy_map.get(ev.evidence_id, False)

        item_score = round((0.35 * src_q) + (0.35 * cnt_q) + (0.30 * rel_q), 2)
        rejection_reasons: List[str] = []

        if is_red:
            item_score = round(item_score * 0.30, 2)
            rejection_reasons.append("Redundant duplicate or near-duplicate evidence")
        if cnt_q < 0.30:
            rejection_reasons.append("Insufficient content quality or text volume")
        if rel_q < 0.20:
            rejection_reasons.append("Low relevance to research topic")
        if src_q < 0.30:
            rejection_reasons.append("Low quality or untrusted source domain")

        is_valid = (item_score >= 0.50) and not is_red and (cnt_q >= 0.30)

        signals = {
            "source_quality": src_q,
            "content_quality": cnt_q,
            "topic_relevance": rel_q,
            "is_redundant": 1.0 if is_red else 0.0,
        }

        evidence_validation_items.append(
            EvidenceValidationItem(
                evidence_id=ev.evidence_id,
                is_valid=is_valid,
                score=item_score,
                signals=signals,
                rejection_reasons=rejection_reasons,
            )
        )

        if is_valid:
            usable_evidence_list.append(ev)

    # Compute overall research validation metrics
    usable_count = len(usable_evidence_list)
    rejected_count = len(all_evidence) - usable_count

    mean_usable_score = (
        sum(item.score for item in evidence_validation_items if item.is_valid) / usable_count
        if usable_count > 0
        else 0.0
    )

    diversity_score = score_source_diversity(usable_evidence_list)
    completeness_score = score_evidence_completeness(usable_evidence_list)

    overall_score = round(
        (0.50 * mean_usable_score) + (0.25 * completeness_score) + (0.25 * diversity_score),
        2,
    )

    if overall_score >= 0.80 and usable_count >= 2:
        quality_classification = "strong"
    elif overall_score >= threshold and usable_count >= 1:
        quality_classification = "acceptable"
    elif overall_score >= 0.40:
        quality_classification = "insufficient"
    else:
        quality_classification = "unusable"

    is_usable = (overall_score >= threshold) and (usable_count >= 1)
    needs_additional_research = quality_classification in ("insufficient", "unusable")

    rationale = (
        f"Research classification: {quality_classification.upper()} (score: {overall_score:.2f}, "
        f"usable evidence: {usable_count}/{len(all_evidence)}, completeness: {completeness_score:.2f}, "
        f"diversity: {diversity_score:.2f})."
    )

    return ResearchValidationResult(
        research_id=research_id,
        topic_id=research.topic_id,
        is_usable=is_usable,
        overall_score=overall_score,
        quality_classification=quality_classification,
        needs_additional_research=needs_additional_research,
        evidence_items=evidence_validation_items,
        usable_evidence_count=usable_count,
        rejected_evidence_count=rejected_count,
        rationale=rationale,
    )
