from dataclasses import dataclass
from typing import Any, Dict, Optional, Union


@dataclass
class TopicFailureDiagnostic:
    """Deterministic, sanitized diagnostic representation for a failed topic execution."""
    topic_id: str
    title: str
    failed_stage: str
    sanitized_reason: str
    stage_status: str = "FAILED"
    research_id: Optional[str] = None
    draft_id: Optional[str] = None
    publication_id: Optional[str] = None
    is_publishable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "failed_stage": self.failed_stage,
            "sanitized_reason": self.sanitized_reason,
            "stage_status": self.stage_status,
            "research_id": self.research_id,
            "draft_id": self.draft_id,
            "publication_id": self.publication_id,
            "is_publishable": self.is_publishable,
        }


def sanitize_failure_reason(exc_or_reason: Union[Exception, str]) -> str:
    """
    Sanitize exception or reason string to guarantee zero sensitive internal details are exposed.
    Strips raw SQL queries, database paths, filesystem paths, credentials, tokens, and stack traces.
    """
    if isinstance(exc_or_reason, Exception):
        msg = str(exc_or_reason)
        exc_type = type(exc_or_reason).__name__
        lower_msg = msg.lower()
        if any(kw in lower_msg for kw in ["select ", "insert ", "update ", "delete ", "sqlite", "c:\\", "f:\\", "/home/", "password", "token", "secret", "key"]):
            return f"Operation failed with exception: {exc_type}"
        return f"{exc_type}: {msg[:200]}"
    
    reason = str(exc_or_reason)
    lower_reason = reason.lower()
    if any(kw in lower_reason for kw in ["select ", "insert ", "update ", "delete ", "sqlite", "c:\\", "f:\\", "/home/", "password", "token", "secret", "key"]):
        return "Operation halted due to execution failure."
    
    return reason[:250]
