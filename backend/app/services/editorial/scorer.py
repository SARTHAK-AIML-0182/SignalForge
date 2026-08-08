import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from app.repositories import TopicData

STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "up", "about", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "it", "its", "this", "that", "these", "those", "how", "why", "what",
    "when", "where", "who", "which", "says", "new", "via"
}


def tokenize(text: str) -> Set[str]:
    """Tokenize text into lowercase alphanumeric words, stripping stop words."""
    words = re.findall(r"\b[a-z0-9_]+\b", text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 1}


def score_relevance(title: str, description: str, domain: str = "AI & Emerging Technology") -> float:
    """Score relevance to NOVA's domain (0.0 to 10.0)."""
    combined = f"{title} {description}".lower()
    
    high_relevance = [
        "ai", "artificial intelligence", "machine learning", "agent", "agents", "llm",
        "neural", "deep learning", "transformer", "nlp", "vision model", "vlm", "robotics",
        "foundation model", "large language model", "generative ai", "diffusion", "embodied ai"
    ]
    secondary_relevance = [
        "gpu", "compute", "cuda", "inference", "fine-tuning", "quantization", "distillation",
        "open-source", "security", "safety", "alignment", "benchmark", "dataset", "framework",
        "developer", "coding", "vulnerability", "model", "models"
    ]
    irrelevant_terms = [
        "stock", "shares", "dividend", "crypto", "nft", "bitcoin", "real estate", "gossip",
        "celebrity", "red carpet", "fashion", "sports", "quarterly earnings"
    ]

    high_matches = sum(1 for term in high_relevance if term in combined)
    secondary_matches = sum(1 for term in secondary_relevance if term in combined)
    irrelevant_matches = sum(1 for term in irrelevant_terms if term in combined)

    if irrelevant_matches > 0 and high_matches == 0:
        return 1.0

    raw_score = (high_matches * 3.5) + (secondary_matches * 1.5) - (irrelevant_matches * 2.0)
    # Bound score between 1.0 and 10.0
    return max(1.0, min(10.0, round(raw_score, 1)))


def score_technical_significance(title: str, description: str) -> float:
    """Score technical depth and architectural significance (0.0 to 10.0)."""
    combined = f"{title} {description}".lower()

    technical_terms = [
        "architecture", "paper", "arxiv", "weights", "training", "algorithm", "zero-shot",
        "few-shot", "reasoning", "multimodal", "quantization", "latency", "throughput",
        "vulnerability", "patch", "agentic", "tool-use", "context window", "attention",
        "flashattention", "benchmark", "distillation", "dataset", "pipeline", "lfm", "model"
    ]
    promotional_terms = [
        "announces logo", "merch", "podcast episode", "opinion", "rumor", "speculation",
        "unveils brand", "celebrity", "sponsorship", "discount", "promo"
    ]

    tech_matches = sum(1 for term in technical_terms if term in combined)
    promo_matches = sum(1 for term in promotional_terms if term in combined)

    raw_score = 4.0 + (tech_matches * 1.5) - (promo_matches * 2.5)
    return max(1.0, min(10.0, round(raw_score, 1)))


def score_potential_impact(title: str, description: str) -> float:
    """Score potential industry or technical impact (0.0 to 10.0)."""
    combined = f"{title} {description}".lower()

    high_impact = [
        "frontier", "breakthrough", "sota", "state-of-the-art", "open-source", "critical",
        "vulnerability", "infrastructure", "release", "standard", "paradigm shift",
        "enterprise", "autonomous", "milestone", "open-source ai"
    ]
    low_impact = [
        "minor bug fix", "incremental update", "teaser", "coming soon", "concept", "fan art",
        "small patch", "tweak"
    ]

    impact_matches = sum(1 for term in high_impact if term in combined)
    low_matches = sum(1 for term in low_impact if term in combined)

    raw_score = 5.0 + (impact_matches * 1.8) - (low_matches * 2.5)
    return max(1.0, min(10.0, round(raw_score, 1)))


def score_novelty(title: str, description: str, existing_topics: Optional[List[TopicData]] = None) -> float:
    """Score novelty by comparing against previously evaluated or stored topics (0.0 to 10.0)."""
    if not existing_topics:
        return 9.5

    current_tokens = tokenize(f"{title} {description}")
    if not current_tokens:
        return 5.0

    max_similarity = 0.0
    for prev in existing_topics:
        prev_tokens = tokenize(f"{prev.title} {prev.description or ''}")
        if not prev_tokens:
            continue
        intersection = current_tokens.intersection(prev_tokens)
        union = current_tokens.union(prev_tokens)
        similarity = len(intersection) / len(union) if union else 0.0
        if similarity > max_similarity:
            max_similarity = similarity

    if max_similarity >= 0.55:
        # High overlap - duplicate/repetitive
        return 1.5
    elif max_similarity >= 0.35:
        # Moderate overlap
        return 4.5
    elif max_similarity >= 0.20:
        return 7.0
    else:
        # High novelty
        return 9.5


def score_persona_alignment(title: str, description: str) -> float:
    """Score alignment with NOVA's editorial philosophy (0.0 to 10.0)."""
    combined = f"{title} {description}".lower()

    alignment_terms = [
        "build", "secure", "deploy", "understand", "interact", "framework", "safety",
        "open-source", "robotics", "infrastructure", "developer", "autonomy", "agents"
    ]

    matches = sum(1 for term in alignment_terms if term in combined)
    raw_score = 4.5 + (matches * 1.2)
    return max(1.0, min(10.0, round(raw_score, 1)))


def score_timeliness(discovered_at: Optional[str]) -> float:
    """Score timeliness based on discovery timestamp (0.0 to 10.0)."""
    if not discovered_at:
        return 7.0

    try:
        dt = datetime.fromisoformat(discovered_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_hours = (now - dt).total_seconds() / 3600.0

        if age_hours <= 24:
            return 9.5
        elif age_hours <= 72:
            return 8.0
        elif age_hours <= 168:  # 7 days
            return 6.5
        else:
            return 4.0
    except Exception:
        return 7.0


def compute_composite_score(
    relevance: float,
    tech_sig: float,
    impact: float,
    novelty: float,
    persona_align: float,
    timeliness: float,
) -> float:
    """
    Weighted scoring model:
    - Relevance: 0.25
    - Technical Significance: 0.25
    - Potential Impact: 0.20
    - Novelty: 0.15
    - Persona Alignment: 0.10
    - Timeliness: 0.05
    """
    weighted_sum = (
        (0.25 * relevance)
        + (0.25 * tech_sig)
        + (0.20 * impact)
        + (0.15 * novelty)
        + (0.10 * persona_align)
        + (0.05 * timeliness)
    )
    return round(weighted_sum, 2)
