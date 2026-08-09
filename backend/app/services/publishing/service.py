import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.services.research.writer import DraftResult
from app.services.publishing.adapters import BasePublishingAdapter, DryRunPublishingAdapter
from app.services.publishing.models import PublicationResult, PublicationStatus


def publish_draft(
    draft: DraftResult,
    adapter: Optional[BasePublishingAdapter] = None,
    dry_run: bool = True,
) -> PublicationResult:
    """
    Enforce final publishability gate and dispatch to publishing adapter.
    Refuses publication if draft.is_publishable is False, content is empty, or traceability is missing.
    Does NOT call adapter when publication is blocked.
    """
    if adapter is None:
        adapter = DryRunPublishingAdapter()

    platform = adapter.platform_name
    now_utc = datetime.now(timezone.utc).isoformat()

    raw_seed = f"{draft.draft_id if draft else 'none'}:{platform}:{dry_run}"
    pub_hash = hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()[:12]
    pub_id = f"pub-{pub_hash}"

    # Pre-eligibility Check 1: Draft presence
    if not draft or not draft.full_text.strip():
        return PublicationResult(
            publication_id=pub_id,
            draft_id=draft.draft_id if draft else "",
            topic_id=draft.topic_id if draft else "",
            research_id=draft.research_id if draft else "",
            platform=platform,
            status=PublicationStatus.BLOCKED,
            is_successful=False,
            is_dry_run=dry_run,
            published_content="",
            published_at=now_utc,
            warnings=["Draft is empty or not provided."],
            error_message="Draft content is empty.",
            traceability={},
            rationale="BLOCKED: Publication refused because draft content is empty.",
        )

    # Pre-eligibility Check 2: Final Publishability Gate
    if not draft.is_publishable:
        return PublicationResult(
            publication_id=pub_id,
            draft_id=draft.draft_id,
            topic_id=draft.topic_id,
            research_id=draft.research_id,
            platform=platform,
            status=PublicationStatus.BLOCKED,
            is_successful=False,
            is_dry_run=dry_run,
            published_content="",
            published_at=now_utc,
            warnings=list(draft.warnings),
            error_message="Draft is marked unpublishable.",
            traceability=dict(draft.traceability),
            rationale=f"BLOCKED: Publication refused because draft is marked unpublishable (is_publishable=False). Rationale: {draft.rationale}",
        )

    # Pre-eligibility Check 3: Traceability presence
    if not draft.traceability or len(draft.sections) == 0:
        return PublicationResult(
            publication_id=pub_id,
            draft_id=draft.draft_id,
            topic_id=draft.topic_id,
            research_id=draft.research_id,
            platform=platform,
            status=PublicationStatus.BLOCKED,
            is_successful=False,
            is_dry_run=dry_run,
            published_content="",
            published_at=now_utc,
            warnings=["Draft lacks required section traceability."],
            error_message="Missing traceability mapping.",
            traceability={},
            rationale="BLOCKED: Publication refused because draft lacks required traceability or sections.",
        )

    # Pre-eligibility Check 4: Blocking warnings
    if len(draft.warnings) > 0:
        return PublicationResult(
            publication_id=pub_id,
            draft_id=draft.draft_id,
            topic_id=draft.topic_id,
            research_id=draft.research_id,
            platform=platform,
            status=PublicationStatus.BLOCKED,
            is_successful=False,
            is_dry_run=dry_run,
            published_content="",
            published_at=now_utc,
            warnings=list(draft.warnings),
            error_message="Draft contains blocking warnings.",
            traceability=dict(draft.traceability),
            rationale=f"BLOCKED: Publication refused due to draft warnings: {', '.join(draft.warnings)}.",
        )

    # Pre-eligibility checks passed -> Dispatch to adapter
    return adapter.publish(draft, dry_run=dry_run)
