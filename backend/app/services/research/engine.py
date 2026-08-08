import logging
import secrets
from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.repositories import (
    BaseEvidenceRepository,
    BaseResearchRepository,
    TopicData,
    get_evidence_repository,
    get_research_repository,
)
from app.services.research.extractor import DEFAULT_HEADERS, extract_page_content, fetch_html
from app.services.research.scorer import compute_research_confidence, score_evidence_confidence

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    research_id: str
    topic_id: str
    status: str
    confidence: float
    evidence_count: int
    completed_at: Optional[str] = None


def research_topic(
    topic: TopicData,
    research_repo: Optional[BaseResearchRepository] = None,
    evidence_repo: Optional[BaseEvidenceRepository] = None,
    http_client: Optional[httpx.Client] = None,
    max_sources: int = 3,
    timeout: float = 10.0,
) -> ResearchResult:
    """
    Autonomously gather supporting evidence for a selected topic from public web sources.
    Parses content, prevents duplicate evidence, calculates deterministic confidence,
    and updates research and evidence records in SQLite.
    """
    if research_repo is None:
        research_repo = get_research_repository()
    if evidence_repo is None:
        evidence_repo = get_evidence_repository()

    # Step 1: Create or retrieve research record
    existing_res = research_repo.get_research_by_topic(topic.topic_id)
    if not existing_res:
        res_id = f"res-{secrets.token_hex(16)}"
        research_data = research_repo.create_research(
            research_id=res_id,
            agent_id=topic.agent_id,
            topic_id=topic.topic_id,
            status="pending",
            confidence=0.0,
        )
    else:
        research_data = existing_res

    # Step 2: Mark research as in_progress
    research_repo.update_research_status(research_data.research_id, "in_progress")

    # Step 3: Collect target source URLs
    target_urls: List[str] = []
    if topic.source_url and topic.source_url.strip():
        target_urls.append(topic.source_url.strip())

    # Limit to max_sources
    target_urls = target_urls[:max_sources]

    client_provided = http_client is not None
    client = http_client if http_client is not None else httpx.Client(timeout=timeout, headers=DEFAULT_HEADERS)

    try:
        for index, url in enumerate(target_urls):
            # Duplicate evidence check by URL within this research investigation
            if evidence_repo.get_evidence_by_url(research_data.research_id, url):
                continue

            html_text = fetch_html(client, url)
            if not html_text:
                continue

            extracted = extract_page_content(html_text, url)
            content = extracted.get("content", "").strip()
            if not content:
                continue

            title = extracted.get("title") or topic.title
            source_name = extracted.get("source_name") or topic.source_name or "Web Source"
            is_primary = (index == 0 and url == topic.source_url)

            ev_confidence = score_evidence_confidence(
                source_url=url,
                is_primary=is_primary,
                content=content,
                title=title,
            )

            evidence_id = f"ev-{secrets.token_hex(16)}"
            evidence_repo.create_evidence(
                evidence_id=evidence_id,
                research_id=research_data.research_id,
                source_url=url,
                source_name=source_name,
                source_type="primary_web" if is_primary else "web",
                title=title,
                content=content,
                confidence=ev_confidence,
            )
    finally:
        if not client_provided:
            client.close()

    # Step 4: Retrieve all collected evidence
    all_evidence = evidence_repo.list_evidence_by_research(research_data.research_id)

    if all_evidence:
        total_confidence = compute_research_confidence(all_evidence)
        completed_res = research_repo.complete_research(
            research_id=research_data.research_id,
            confidence=total_confidence,
            status="completed",
        )
        return ResearchResult(
            research_id=completed_res.research_id,
            topic_id=topic.topic_id,
            status="completed",
            confidence=completed_res.confidence,
            evidence_count=len(all_evidence),
            completed_at=completed_res.completed_at,
        )
    else:
        research_repo.update_research_status(research_data.research_id, "failed")
        return ResearchResult(
            research_id=research_data.research_id,
            topic_id=topic.topic_id,
            status="failed",
            confidence=0.0,
            evidence_count=0,
            completed_at=None,
        )
