import html
import re
import secrets
from dataclasses import dataclass, field
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
from app.services.research.validation import (
    tokenize,
    validate_research,
)


@dataclass
class SynthesizedFinding:
    finding_id: str
    text: str
    evidence_ids: List[str]
    source_urls: List[str]
    confidence: float
    support_count: int


@dataclass
class ResearchSynthesisResult:
    research_id: str
    topic_id: str
    topic_title: str
    is_usable: bool
    quality_classification: str  # "strong", "acceptable", "insufficient", "unusable"
    overall_score: float
    findings: List[SynthesizedFinding]
    source_references: List[Dict[str, str]]
    source_diversity_count: int
    distinct_domains: List[str]
    detected_conflicts: List[str]
    limitations: List[str]
    confidence: float
    rationale: str


def split_into_sentences(text: str) -> List[str]:
    """Split raw text into clean candidate sentences."""
    if not text:
        return []
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    cleaned: List[str] = []
    for s in raw_sentences:
        st = s.strip()
        if 35 <= len(st) <= 250 and not st.startswith(("<", "http", "{", "[")):
            cleaned.append(st)
    return cleaned


def detect_conflicts(sentences: List[str]) -> List[str]:
    """Detect opposing numeric metrics or explicit negation statements among sentences."""
    conflicts: List[str] = []

    numeric_claims: Dict[str, str] = {}
    for s in sentences:
        # Match metric patterns like "accuracy 95%", "speed 10x"
        matches = re.findall(r"\b([a-z_]+)\s+(\d+(?:\.\d+)?%?|\d+x)\b", s.lower())
        for metric, val in matches:
            if metric in numeric_claims and numeric_claims[metric] != val:
                conflicts.append(
                    f"Conflicting metric for '{metric}': '{numeric_claims[metric]}' vs '{val}'."
                )
            else:
                numeric_claims[metric] = val

    negation_patterns = [
        (r"\b(achieved|succeeded|proven|supported)\b", r"\b(failed|denied|unproven|disproven)\b")
    ]
    for pos_pat, neg_pat in negation_patterns:
        pos_s = [s for s in sentences if re.search(pos_pat, s, re.IGNORECASE)]
        neg_s = [s for s in sentences if re.search(neg_pat, s, re.IGNORECASE)]
        if pos_s and neg_s:
            conflicts.append("Opposing claims detected regarding research claims or outcomes.")

    return list(set(conflicts))


def synthesize_research(
    research_id: str,
    max_findings: int = 5,
    validation_threshold: float = 0.65,
    research_repo: Optional[BaseResearchRepository] = None,
    evidence_repo: Optional[BaseEvidenceRepository] = None,
    topic_repo: Optional[BaseTopicRepository] = None,
) -> ResearchSynthesisResult:
    """
    Synthesize validated evidence into a structured, source-grounded research intelligence package.
    Ensures findings are traceable to evidence IDs and source URLs, handles duplicate merging,
    detects conflicts, and respects research validation quality classifications.
    """
    if research_repo is None:
        research_repo = get_research_repository()
    if evidence_repo is None:
        evidence_repo = get_evidence_repository()
    if topic_repo is None:
        topic_repo = get_topic_repository()

    val_result = validate_research(
        research_id=research_id,
        research_repo=research_repo,
        evidence_repo=evidence_repo,
        topic_repo=topic_repo,
        threshold=validation_threshold,
    )

    topic = topic_repo.get_topic(val_result.topic_id)
    topic_title = topic.title if topic else ""
    topic_desc = topic.description if topic else ""

    # Refuse synthesis for unusable research
    if val_result.quality_classification == "unusable" or (not val_result.is_usable and val_result.quality_classification != "insufficient"):
        return ResearchSynthesisResult(
            research_id=research_id,
            topic_id=val_result.topic_id,
            topic_title=topic_title,
            is_usable=False,
            quality_classification="unusable",
            overall_score=val_result.overall_score,
            findings=[],
            source_references=[],
            source_diversity_count=0,
            distinct_domains=[],
            detected_conflicts=[],
            limitations=["Research validation classified research package as UNUSABLE."],
            confidence=0.0,
            rationale=f"REFUSED: Research validation classified topic as UNUSABLE.",
        )

    # Filter validated evidence only
    valid_ev_ids = {item.evidence_id for item in val_result.evidence_items if item.is_valid}
    ev_score_map = {item.evidence_id: item.score for item in val_result.evidence_items if item.is_valid}

    all_evidence = evidence_repo.list_evidence_by_research(research_id)
    validated_evidence = [e for e in all_evidence if e.evidence_id in valid_ev_ids]

    topic_tokens = tokenize(f"{topic_title} {topic_desc}")

    candidate_sentences: List[Dict] = []
    all_extracted_sentences: List[str] = []

    for ev in validated_evidence:
        sentences = split_into_sentences(ev.content)
        ev_score = ev_score_map.get(ev.evidence_id, 0.50)

        for s in sentences:
            all_extracted_sentences.append(s)
            s_tokens = tokenize(s)
            overlap = (
                len(topic_tokens.intersection(s_tokens)) / len(topic_tokens)
                if topic_tokens
                else 0.0
            )
            sentence_score = round(
                (0.45 * overlap) + (0.35 * ev_score) + (0.20 * min(1.0, len(s_tokens) / 15)),
                2,
            )
            candidate_sentences.append(
                {"text": s, "score": sentence_score, "evidence": ev, "tokens": s_tokens}
            )

    # Sort candidate sentences by score descending
    candidate_sentences.sort(key=lambda x: x["score"], reverse=True)

    findings: List[SynthesizedFinding] = []

    for cand in candidate_sentences:
        c_tokens = cand["tokens"]
        if not c_tokens:
            continue

        matched_finding = None
        for f in findings:
            f_tokens = tokenize(f.text)
            union = c_tokens.union(f_tokens)
            intersection = c_tokens.intersection(f_tokens)
            similarity = len(intersection) / len(union) if union else 0.0

            if similarity >= 0.50:
                matched_finding = f
                break

        ev = cand["evidence"]
        if matched_finding:
            # Merge into existing finding
            if ev.evidence_id not in matched_finding.evidence_ids:
                matched_finding.evidence_ids.append(ev.evidence_id)
            if ev.source_url not in matched_finding.source_urls:
                matched_finding.source_urls.append(ev.source_url)
            matched_finding.support_count += 1

            # Check distinct domains for finding
            f_domains = {
                urlparse(u).netloc.lower().replace("www.", "")
                for u in matched_finding.source_urls
                if u
            }
            if len(f_domains) > 1:
                matched_finding.confidence = min(
                    0.98, round(matched_finding.confidence + 0.08 * (len(f_domains) - 1), 2)
                )
        else:
            if len(findings) < max_findings:
                f_id = f"find-{secrets.token_hex(8)}"
                findings.append(
                    SynthesizedFinding(
                        finding_id=f_id,
                        text=cand["text"],
                        evidence_ids=[ev.evidence_id],
                        source_urls=[ev.source_url],
                        confidence=round(ev.confidence, 2),
                        support_count=1,
                    )
                )

    # Source references & distinct domains
    source_references: List[Dict[str, str]] = []
    domain_set: Set[str] = set()

    for ev in validated_evidence:
        domain = urlparse(ev.source_url).netloc.lower().replace("www.", "") if ev.source_url else "Web Source"
        if domain:
            domain_set.add(domain)
        source_references.append(
            {
                "evidence_id": ev.evidence_id,
                "source_name": ev.source_name,
                "source_url": ev.source_url,
                "domain": domain,
            }
        )

    distinct_domains = sorted(list(domain_set))
    source_diversity_count = len(distinct_domains)

    detected_conflicts = detect_conflicts(all_extracted_sentences)

    limitations: List[str] = []
    if source_diversity_count < 2:
        limitations.append("Low source diversity: evidence originates from a single domain.")
    if len(validated_evidence) < 2:
        limitations.append("Concentrated sourcing: limited total evidence volume available.")
    if val_result.quality_classification in ("insufficient", "unusable"):
        limitations.append("Research quality classified as INSUFFICIENT; additional research recommended.")
    if detected_conflicts:
        limitations.append("Potential conflicting or contradictory statements detected across sources.")

    is_usable = (val_result.quality_classification in ("strong", "acceptable")) and len(findings) > 0

    overall_confidence = (
        round(sum(f.confidence for f in findings) / len(findings), 2)
        if findings
        else 0.0
    )

    if val_result.quality_classification == "insufficient":
        rationale = (
            f"INCOMPLETE SYNTHESIS (classification: INSUFFICIENT, score: {val_result.overall_score:.2f}). "
            f"Extracted {len(findings)} findings from {len(validated_evidence)} validated items. Additional research required."
        )
    else:
        rationale = (
            f"VALIDATED SYNTHESIS PACKAGE (classification: {val_result.quality_classification.upper()}, score: {val_result.overall_score:.2f}). "
            f"Extracted {len(findings)} findings from {len(validated_evidence)} validated evidence items across {source_diversity_count} distinct domains."
        )

    return ResearchSynthesisResult(
        research_id=research_id,
        topic_id=val_result.topic_id,
        topic_title=topic_title,
        is_usable=is_usable,
        quality_classification=val_result.quality_classification,
        overall_score=val_result.overall_score,
        findings=findings,
        source_references=source_references,
        source_diversity_count=source_diversity_count,
        distinct_domains=distinct_domains,
        detected_conflicts=detected_conflicts,
        limitations=limitations,
        confidence=overall_confidence,
        rationale=rationale,
    )
