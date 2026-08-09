import secrets
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.repositories import (
    BaseAgentRepository,
    BaseEvidenceRepository,
    BaseResearchRepository,
    BaseTopicRepository,
    get_agent_repository,
    get_evidence_repository,
    get_research_repository,
    get_topic_repository,
)
from app.services.research.synthesis import (
    ResearchSynthesisResult,
    SynthesizedFinding,
    synthesize_research,
)


@dataclass
class SupportedClaim:
    claim_id: str
    claim_text: str
    finding_ids: List[str]
    evidence_ids: List[str]
    source_urls: List[str]
    confidence: float


@dataclass
class WritingConstraint:
    rule_id: str
    rule_type: str
    description: str
    is_mandatory: bool = True


@dataclass
class ContentBriefResult:
    research_id: str
    topic_id: str
    topic_title: str
    angle: str
    audience: Dict[str, str]
    claims: List[SupportedClaim]
    findings: List[SynthesizedFinding]
    sources: List[Dict[str, str]]
    limitations: List[str]
    constraints: List[WritingConstraint]
    confidence: float
    is_usable: bool
    rationale: str


def build_writing_constraints() -> List[WritingConstraint]:
    """Build structured mandatory writing constraints for future LLM generation."""
    return [
        WritingConstraint(
            rule_id="rule-001",
            rule_type="factual_integrity",
            description="Do not invent unsupported facts or external information not present in the brief.",
            is_mandatory=True,
        ),
        WritingConstraint(
            rule_id="rule-002",
            rule_type="evidence_validation",
            description="Do not cite or reference rejected or unvalidated evidence.",
            is_mandatory=True,
        ),
        WritingConstraint(
            rule_id="rule-003",
            rule_type="transparency",
            description="Do not hide or ignore documented research limitations.",
            is_mandatory=True,
        ),
        WritingConstraint(
            rule_id="rule-004",
            rule_type="confidence_accuracy",
            description="Do not overstate confidence or present uncertain claims as definitive.",
            is_mandatory=True,
        ),
        WritingConstraint(
            rule_id="rule-005",
            rule_type="traceability",
            description="Maintain factual claim-to-source traceability for every key statement.",
            is_mandatory=True,
        ),
        WritingConstraint(
            rule_id="rule-006",
            rule_type="diversity_honesty",
            description="Do not claim independent confirmation when evidence originates from the same source domain.",
            is_mandatory=True,
        ),
    ]


def build_content_angle(topic_title: str, topic_desc: str, synthesis: ResearchSynthesisResult) -> str:
    """Derive content angle deterministically from topic and synthesis results."""
    if synthesis.findings:
        top_text = synthesis.findings[0].text
        return (
            f"Technical analysis of '{topic_title}': Focus on key insight '{top_text}' "
            f"supported by {len(synthesis.findings)} findings across {synthesis.source_diversity_count} distinct domain(s)."
        )
    return (
        f"Evidence-backed analysis of '{topic_title}' focusing on technical developments in "
        f"{topic_desc or 'emerging technology'}."
    )


def build_audience_context(agent_name: Optional[str], agent_domain: Optional[str]) -> Dict[str, str]:
    """Derive target audience and domain context from persona identity."""
    return {
        "target_persona": agent_name or "NOVA",
        "primary_domain": agent_domain or "AI & Emerging Tech",
        "technical_depth": "Technical / Architectural Focus",
    }


def build_supported_claims(findings: List[SynthesizedFinding]) -> List[SupportedClaim]:
    """Map synthesized findings to supported claims preserving full 4-level traceability."""
    claims: List[SupportedClaim] = []
    for f in findings:
        c_id = f"claim-{secrets.token_hex(8)}"
        claims.append(
            SupportedClaim(
                claim_id=c_id,
                claim_text=f.text,
                finding_ids=[f.finding_id],
                evidence_ids=list(f.evidence_ids),
                source_urls=list(f.source_urls),
                confidence=f.confidence,
            )
        )
    return claims


def build_content_brief(
    research_id: str,
    max_claims: int = 5,
    validation_threshold: float = 0.65,
    research_repo: Optional[BaseResearchRepository] = None,
    evidence_repo: Optional[BaseEvidenceRepository] = None,
    topic_repo: Optional[BaseTopicRepository] = None,
    agent_repo: Optional[BaseAgentRepository] = None,
) -> ContentBriefResult:
    """
    Convert a validated ResearchSynthesisResult into a structured, source-grounded Content Brief.
    Forms a clean boundary between Research Intelligence and future Writing subsystems.
    """
    if research_repo is None:
        research_repo = get_research_repository()
    if evidence_repo is None:
        evidence_repo = get_evidence_repository()
    if topic_repo is None:
        topic_repo = get_topic_repository()
    if agent_repo is None:
        agent_repo = get_agent_repository()

    syn_result = synthesize_research(
        research_id=research_id,
        max_findings=max_claims,
        validation_threshold=validation_threshold,
        research_repo=research_repo,
        evidence_repo=evidence_repo,
        topic_repo=topic_repo,
    )

    topic = topic_repo.get_topic(syn_result.topic_id)
    topic_desc = topic.description if topic else ""
    agent_id = topic.agent_id if topic else ""
    agent = agent_repo.get_agent(agent_id) if agent_id else None

    agent_name = agent.name if agent else "NOVA"
    agent_domain = agent.domain if agent else "AI & Emerging Tech"

    constraints = build_writing_constraints()
    audience = build_audience_context(agent_name, agent_domain)

    # Refuse brief generation for unusable research
    if syn_result.quality_classification == "unusable" or (not syn_result.is_usable and syn_result.quality_classification != "insufficient"):
        return ContentBriefResult(
            research_id=research_id,
            topic_id=syn_result.topic_id,
            topic_title=syn_result.topic_title,
            angle=f"UNUSABLE: No angle available for '{syn_result.topic_title}'.",
            audience=audience,
            claims=[],
            findings=[],
            sources=[],
            limitations=["Underlying research is UNUSABLE."],
            constraints=constraints,
            confidence=0.0,
            is_usable=False,
            rationale=f"REFUSED: Content brief cannot be generated for UNUSABLE research.",
        )

    claims = build_supported_claims(syn_result.findings)
    angle = build_content_angle(syn_result.topic_title, topic_desc, syn_result)

    if syn_result.quality_classification == "insufficient":
        return ContentBriefResult(
            research_id=research_id,
            topic_id=syn_result.topic_id,
            topic_title=syn_result.topic_title,
            angle=angle,
            audience=audience,
            claims=claims,
            findings=syn_result.findings,
            sources=syn_result.source_references,
            limitations=syn_result.limitations,
            constraints=constraints,
            confidence=syn_result.confidence,
            is_usable=False,
            rationale=f"INCOMPLETE CONTENT BRIEF (classification: INSUFFICIENT, score: {syn_result.overall_score:.2f}). Additional research required.",
        )

    is_usable = syn_result.is_usable and len(claims) > 0

    rationale = (
        f"VALIDATED CONTENT BRIEF (classification: {syn_result.quality_classification.upper()}, "
        f"score: {syn_result.overall_score:.2f}). {len(claims)} supported claims ready for writing."
    )

    return ContentBriefResult(
        research_id=research_id,
        topic_id=syn_result.topic_id,
        topic_title=syn_result.topic_title,
        angle=angle,
        audience=audience,
        claims=claims,
        findings=syn_result.findings,
        sources=syn_result.source_references,
        limitations=syn_result.limitations,
        constraints=constraints,
        confidence=syn_result.confidence,
        is_usable=is_usable,
        rationale=rationale,
    )
