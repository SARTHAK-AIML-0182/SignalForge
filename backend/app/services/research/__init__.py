"""Autonomous Research & Evidence Collection Engine package for SignalForge."""

from app.services.research.content_brief import (
    ContentBriefResult,
    SupportedClaim,
    WritingConstraint,
    build_content_brief,
)
from app.services.research.engine import ResearchResult, research_topic
from app.services.research.extractor import extract_page_content, fetch_html
from app.services.research.scorer import compute_research_confidence, score_evidence_confidence
from app.services.research.synthesis import (
    ResearchSynthesisResult,
    SynthesizedFinding,
    synthesize_research,
)
from app.services.research.validation import (
    EvidenceValidationItem,
    ResearchValidationResult,
    detect_redundancy,
    score_content_quality,
    score_evidence_completeness,
    score_source_diversity,
    score_source_quality,
    score_topic_relevance,
    validate_research,
)

__all__ = [
    "ResearchResult",
    "research_topic",
    "fetch_html",
    "extract_page_content",
    "score_evidence_confidence",
    "compute_research_confidence",
    "EvidenceValidationItem",
    "ResearchValidationResult",
    "validate_research",
    "score_source_quality",
    "score_content_quality",
    "score_topic_relevance",
    "detect_redundancy",
    "score_source_diversity",
    "score_evidence_completeness",
    "SynthesizedFinding",
    "ResearchSynthesisResult",
    "synthesize_research",
    "SupportedClaim",
    "WritingConstraint",
    "ContentBriefResult",
    "build_content_brief",
]
