from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.repositories.persona_repository import AgentPersonaData
from app.repositories.topic_repository import TopicData


@dataclass
class PersonaAlignmentDecision:
    topic_id: str
    aligned: bool
    relevance_score: float
    min_threshold: float
    matched_keywords: List[str] = field(default_factory=list)
    excluded_keywords: List[str] = field(default_factory=list)
    matched_categories: List[str] = field(default_factory=list)
    excluded_categories: List[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "aligned": self.aligned,
            "relevance_score": self.relevance_score,
            "min_threshold": self.min_threshold,
            "matched_keywords": self.matched_keywords,
            "excluded_keywords": self.excluded_keywords,
            "matched_categories": self.matched_categories,
            "excluded_categories": self.excluded_categories,
            "rationale": self.rationale,
        }


def evaluate_topic_alignment(
    topic: TopicData,
    persona: AgentPersonaData,
) -> PersonaAlignmentDecision:
    """
    Deterministically evaluate whether a discovered topic aligns with an agent persona.

    Scoring Model:
    - Primary domain match in topic content: +0.50
    - Secondary domain match in topic content: +0.40 (if primary missed)
    - Baseline general relevance: +0.20
    - Preferred keywords match: +0.10 per match (max +0.30)
    - Preferred categories match: +0.10 per match (max +0.20)
    - Excluded keywords match: -0.50 penalty per match
    - Excluded categories match: -0.50 penalty per match
    - Score clamped strictly between 0.0 and 1.0.

    Alignment Rule:
    - aligned = (relevance_score >= persona.min_relevance_threshold) and not (excluded_keywords or excluded_categories)
    """
    topic_text = f"{topic.title} {topic.description or ''} {topic.source_name or ''}".lower()

    matched_kw: List[str] = []
    excluded_kw: List[str] = []
    matched_cat: List[str] = []
    excluded_cat: List[str] = []

    # 1. Excluded Keyword Check
    for kw in persona.excluded_keywords:
        if kw.strip() and kw.strip().lower() in topic_text:
            excluded_kw.append(kw.strip())

    # 2. Excluded Category Check
    for cat in persona.excluded_categories:
        if cat.strip() and cat.strip().lower() in topic_text:
            excluded_cat.append(cat.strip())

    # 3. Domain Matching
    score = 0.20  # Base score
    domain_match_type = "baseline"

    p_domain = (persona.primary_domain or "").lower().strip()
    if p_domain and p_domain in topic_text:
        score += 0.50
        domain_match_type = f"primary domain ('{persona.primary_domain}')"
    else:
        sec_matched = False
        for sec in persona.secondary_domains:
            sec_clean = sec.lower().strip()
            if sec_clean and sec_clean in topic_text:
                score += 0.40
                domain_match_type = f"secondary domain ('{sec}')"
                sec_matched = True
                break

    # 4. Preferred Keywords Match (max +0.30)
    kw_bonus = 0.0
    for kw in persona.preferred_keywords:
        kw_clean = kw.lower().strip()
        if kw_clean and kw_clean in topic_text:
            matched_kw.append(kw.strip())
            if kw_bonus < 0.30:
                kw_bonus += 0.10
    score += kw_bonus

    # 5. Preferred Categories Match (max +0.20)
    cat_bonus = 0.0
    for cat in persona.preferred_categories:
        cat_clean = cat.lower().strip()
        if cat_clean and cat_clean in topic_text:
            matched_cat.append(cat.strip())
            if cat_bonus < 0.20:
                cat_bonus += 0.10
    score += cat_bonus

    # 6. Excluded Penalties
    if excluded_kw:
        score -= 0.50 * len(excluded_kw)
    if excluded_cat:
        score -= 0.50 * len(excluded_cat)

    # 7. Clamp Score
    final_score = max(0.0, min(1.0, round(score, 2)))
    min_thresh = persona.min_relevance_threshold

    aligned = (final_score >= min_thresh) and not (excluded_kw or excluded_cat)

    # 8. Rationale Construction
    rationale_parts = [f"Relevance score {final_score:.2f} (threshold {min_thresh:.2f}). Domain: {domain_match_type}."]
    if matched_kw:
        rationale_parts.append(f"Matched preferred keywords: {matched_kw}.")
    if matched_cat:
        rationale_parts.append(f"Matched preferred categories: {matched_cat}.")
    if excluded_kw:
        rationale_parts.append(f"REJECTED due to excluded keywords: {excluded_kw}.")
    if excluded_cat:
        rationale_parts.append(f"REJECTED due to excluded categories: {excluded_cat}.")

    if not aligned and not (excluded_kw or excluded_cat):
        rationale_parts.append("REJECTED: Relevance score fell below minimum threshold.")
    elif aligned:
        rationale_parts.append("APPROVED: Topic aligns cleanly with persona configuration.")

    return PersonaAlignmentDecision(
        topic_id=topic.topic_id,
        aligned=aligned,
        relevance_score=final_score,
        min_threshold=min_thresh,
        matched_keywords=matched_kw,
        excluded_keywords=excluded_kw,
        matched_categories=matched_cat,
        excluded_categories=excluded_cat,
        rationale=" ".join(rationale_parts),
    )
