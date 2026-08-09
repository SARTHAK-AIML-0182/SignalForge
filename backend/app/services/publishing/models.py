from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


class PublicationStatus:
    BLOCKED = "blocked"
    DRY_RUN = "dry_run"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class PublicationResult:
    publication_id: str
    draft_id: str
    topic_id: str
    research_id: str
    platform: str
    status: str  # "blocked", "dry_run", "published", "failed"
    is_successful: bool
    is_dry_run: bool
    published_content: str
    published_at: str
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    traceability: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    rationale: str = ""
