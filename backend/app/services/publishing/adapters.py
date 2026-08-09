import hashlib
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.services.research.writer import DraftResult
from app.services.publishing.models import PublicationResult, PublicationStatus


class BasePublishingAdapter(ABC):
    """Abstract base class for platform-independent publishing adapters."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the target platform name (e.g. 'dry_run_local', 'linkedin', 'x')."""
        pass

    @abstractmethod
    def publish(self, draft: DraftResult, dry_run: bool = True) -> PublicationResult:
        """Publish or simulate publication of a DraftResult."""
        pass


class DryRunPublishingAdapter(BasePublishingAdapter):
    """
    Deterministic local dry-run adapter.
    Simulates the publishing boundary without contacting any external web service or API.
    """

    @property
    def platform_name(self) -> str:
        return "dry_run_local"

    def publish(self, draft: DraftResult, dry_run: bool = True) -> PublicationResult:
        # Generate deterministic publication ID based on draft_id, platform, and mode
        raw_seed = f"{draft.draft_id}:{self.platform_name}:{dry_run}"
        pub_hash = hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()[:12]
        publication_id = f"pub-{pub_hash}"

        now_utc = datetime.now(timezone.utc).isoformat()

        status = PublicationStatus.DRY_RUN if dry_run else PublicationStatus.PUBLISHED
        is_dry_run = dry_run

        rationale = (
            f"DRY-RUN SUCCESS: Local dry-run publishing simulation completed for draft '{draft.draft_id}' "
            f"on platform '{self.platform_name}'. Zero external network requests performed."
        )

        return PublicationResult(
            publication_id=publication_id,
            draft_id=draft.draft_id,
            topic_id=draft.topic_id,
            research_id=draft.research_id,
            platform=self.platform_name,
            status=status,
            is_successful=True,
            is_dry_run=is_dry_run,
            published_content=draft.full_text,
            published_at=now_utc,
            warnings=list(draft.warnings),
            error_message=None,
            traceability=dict(draft.traceability),
            rationale=rationale,
        )
