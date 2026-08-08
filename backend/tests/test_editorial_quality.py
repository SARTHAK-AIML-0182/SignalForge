from app.services.editorial.scorer import (
    score_relevance,
    score_technical_significance,
)


def test_strong_agent_topic_is_highly_relevant():
    score = score_relevance(
        "Inside VAKRA: Reasoning, Tool Use, and Failure Modes of Agents",
        "A technical analysis of agent reasoning, tool use, benchmarks, and failure modes.",
    )

    assert score >= 8.0


def test_technical_ai_topic_has_strong_technical_score():
    score = score_technical_significance(
        "Training and Finetuning Sparse Embedding Models",
        "Training architecture, optimization, inference and model evaluation.",
    )

    assert score >= 7.0


def test_generic_business_acquisition_should_not_look_highly_technical():
    score = score_technical_significance(
        "Klaviyo acquires Elias Torres' Agency in full-circle reunion for tech founders",
        "Klaviyo acquired an agency in a business-focused deal involving technology founders.",
    )

    assert score < 6.0

from app.services.editorial.engine import evaluate_topic
from app.repositories import TopicData


def test_generic_business_news_should_not_be_selected():
    topic = TopicData(
        topic_id="test-business-topic",
        agent_id="test-agent",
        title="Klaviyo acquires Elias Torres' Agency in full-circle reunion for tech founders",
        description=(
            "Klaviyo acquired an agency in a business-focused deal involving "
            "technology founders and AI-related products."
        ),
        source_url="https://example.com/business",
        source_name="Tech News",
        discovered_at="2026-08-08T15:00:00+00:00",
        editorial_score=0.0,
        status="discovered",
        rationale=None,
    )

    decision = evaluate_topic(
        topic,
        threshold=6.5,
    )

    assert decision.decision == "rejected"