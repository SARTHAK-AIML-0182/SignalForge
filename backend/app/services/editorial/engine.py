from dataclasses import dataclass
from typing import Dict, List, Optional

from app.repositories import BaseTopicRepository, TopicData, get_topic_repository
from app.services.editorial.scorer import (
    compute_composite_score,
    score_novelty,
    score_persona_alignment,
    score_potential_impact,
    score_relevance,
    score_technical_significance,
    score_timeliness,
)


@dataclass
class EditorialDecision:
    topic_id: str
    decision: str  # "selected" or "rejected"
    total_score: float
    factors: Dict[str, float]
    rationale: str


def evaluate_topic(
    topic: TopicData,
    persona: Optional[Dict] = None,
    existing_topics: Optional[List[TopicData]] = None,
    threshold: float = 6.5,
) -> EditorialDecision:
    """
    Evaluate a single topic against NOVA's editorial identity and scoring model.
    Returns an EditorialDecision containing the composite score, decision, factors, and rationale.
    """
    persona_domain = (persona.get("domain") if persona else None) or "AI & Emerging Technology"

    rel_score = score_relevance(topic.title, topic.description or "", domain=persona_domain)
    tech_score = score_technical_significance(topic.title, topic.description or "")
    impact_score = score_potential_impact(topic.title, topic.description or "")
    nov_score = score_novelty(topic.title, topic.description or "", existing_topics)
    align_score = score_persona_alignment(topic.title, topic.description or "")
    time_score = score_timeliness(topic.discovered_at)

    total_score = compute_composite_score(
        relevance=rel_score,
        tech_sig=tech_score,
        impact=impact_score,
        novelty=nov_score,
        persona_align=align_score,
        timeliness=time_score,
    )

    is_selected = total_score >= threshold
    decision_str = "selected" if is_selected else "rejected"

    factors = {
        "relevance": rel_score,
        "technical_significance": tech_score,
        "potential_impact": impact_score,
        "novelty": nov_score,
        "persona_alignment": align_score,
        "timeliness": time_score,
    }

    if is_selected:
        rationale = (
            f"SELECTED (score {total_score:.2f} >= threshold {threshold:.2f}): "
            f"High relevance ({rel_score}) and technical significance ({tech_score}) "
            f"matching NOVA's focus on AI and emerging technology."
        )
    else:
        rationale = (
            f"REJECTED (score {total_score:.2f} < threshold {threshold:.2f}): "
            f"Insufficient technical depth or novelty (relevance: {rel_score}, "
            f"tech_sig: {tech_score}, novelty: {nov_score})."
        )

    return EditorialDecision(
        topic_id=topic.topic_id,
        decision=decision_str,
        total_score=total_score,
        factors=factors,
        rationale=rationale,
    )


def evaluate_agent_topics(
    agent_id: str,
    repo: Optional[BaseTopicRepository] = None,
    threshold: float = 6.5,
) -> List[EditorialDecision]:
    """
    Evaluate all un-evaluated topics (status='discovered') for an agent.
    Updates SQLite topic records with decision status ('selected'/'rejected'), score, and rationale.
    """
    if repo is None:
        repo = get_topic_repository()

    all_topics = repo.list_topics_by_agent(agent_id)
    unevaluated = [t for t in all_topics if t.status == "discovered"]
    evaluated_topics = [t for t in all_topics if t.status in ("selected", "rejected")]

    decisions: List[EditorialDecision] = []

    for topic in unevaluated:
        decision = evaluate_topic(topic, existing_topics=evaluated_topics, threshold=threshold)
        
        # Persist editorial decision in SQLite
        updated = repo.update_editorial_decision(
            topic_id=topic.topic_id,
            status=decision.decision,
            editorial_score=decision.total_score,
            rationale=decision.rationale,
        )

        if updated:
            evaluated_topics.append(updated)

        decisions.append(decision)

    return decisions
