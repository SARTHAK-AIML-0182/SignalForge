from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


ALLOWED_PUBLICATION_MODES = {"dry_run", "disabled"}
DEFAULT_MAX_TOPICS = 5
MAX_TOPICS_LIMIT = 10


@dataclass
class WorkflowPolicy:
    max_topics: int = DEFAULT_MAX_TOPICS
    editorial_threshold: float = 0.65
    enable_dry_run_publication: bool = True
    publication_mode: str = "dry_run"
    max_topics_upper_bound: int = MAX_TOPICS_LIMIT
    validation_threshold: float = 0.65
    max_research_items: int = 3

    def validate(self) -> "WorkflowPolicy":
        """
        Validate workflow policy parameters deterministically.
        Raises ValueError with human-readable error detail if invalid.
        """
        if isinstance(self.max_topics, bool) or not isinstance(self.max_topics, int):
            raise ValueError("max_topics must be an integer.")
        if self.max_topics < 1:
            raise ValueError(f"max_topics must be at least 1 (got {self.max_topics}).")
        if self.max_topics > self.max_topics_upper_bound:
            raise ValueError(
                f"max_topics cannot exceed safe maximum of {self.max_topics_upper_bound} (got {self.max_topics})."
            )

        if isinstance(self.editorial_threshold, bool) or not isinstance(
            self.editorial_threshold, (int, float)
        ):
            raise ValueError("editorial_threshold must be a numeric value.")
        
        # Support both 0.0-1.0 fraction scale and 0.0-10.0 score scale safely
        if self.editorial_threshold < 0.0 or self.editorial_threshold > 10.0:
            raise ValueError(
                f"editorial_threshold must be between 0.0 and 1.0 (or 0.0 and 10.0 scale) (got {self.editorial_threshold})."
            )

        if isinstance(self.validation_threshold, bool) or not isinstance(
            self.validation_threshold, (int, float)
        ):
            raise ValueError("validation_threshold must be a numeric value.")
        if self.validation_threshold < 0.0 or self.validation_threshold > 1.0:
            raise ValueError(
                f"validation_threshold must be between 0.0 and 1.0 (got {self.validation_threshold})."
            )

        if isinstance(self.max_research_items, bool) or not isinstance(
            self.max_research_items, int
        ):
            raise ValueError("max_research_items must be an integer.")
        if self.max_research_items < 1 or self.max_research_items > 10:
            raise ValueError(
                f"max_research_items must be between 1 and 10 (got {self.max_research_items})."
            )

        mode = (self.publication_mode or "").lower().strip()
        if mode not in ALLOWED_PUBLICATION_MODES:
            raise ValueError(
                f"Unsupported publication_mode '{self.publication_mode}'. "
                f"Allowed modes are: {sorted(list(ALLOWED_PUBLICATION_MODES))}."
            )

        if not self.enable_dry_run_publication and mode == "dry_run":
            # If dry-run publication is explicitly disabled via boolean, set mode to disabled
            self.publication_mode = "disabled"
        elif self.enable_dry_run_publication and mode == "disabled":
            self.enable_dry_run_publication = False

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy to dictionary for JSON persistence and API contracts."""
        return {
            "max_topics": self.max_topics,
            "editorial_threshold": self.editorial_threshold,
            "enable_dry_run_publication": self.enable_dry_run_publication,
            "publication_mode": self.publication_mode,
            "max_topics_upper_bound": self.max_topics_upper_bound,
            "validation_threshold": self.validation_threshold,
            "max_research_items": self.max_research_items,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "WorkflowPolicy":
        """Reconstruct WorkflowPolicy from dictionary, falling back to safe defaults."""
        if not data or not isinstance(data, dict):
            return cls()

        return cls(
            max_topics=int(data.get("max_topics", DEFAULT_MAX_TOPICS)),
            editorial_threshold=float(data.get("editorial_threshold", 0.65)),
            enable_dry_run_publication=bool(data.get("enable_dry_run_publication", True)),
            publication_mode=str(data.get("publication_mode", "dry_run")),
            max_topics_upper_bound=int(data.get("max_topics_upper_bound", MAX_TOPICS_LIMIT)),
            validation_threshold=float(data.get("validation_threshold", 0.65)),
            max_research_items=int(data.get("max_research_items", 3)),
        )


def resolve_workflow_policy(
    request_config: Optional[Any] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> WorkflowPolicy:
    """
    Deterministically resolve effective WorkflowPolicy from conservative defaults,
    optional WorkflowConfig / WorkflowPolicy instance, and optional override dictionary.
    Calls validate() before returning.
    """
    policy = WorkflowPolicy()

    if request_config is not None:
        if isinstance(request_config, WorkflowPolicy):
            policy = request_config
        elif hasattr(request_config, "max_topics"):
            policy.max_topics = getattr(request_config, "max_topics", policy.max_topics)
            policy.editorial_threshold = getattr(
                request_config, "editorial_threshold", policy.editorial_threshold
            )
            policy.enable_dry_run_publication = getattr(
                request_config,
                "enable_dry_run_publication",
                policy.enable_dry_run_publication,
            )
            policy.publication_mode = getattr(
                request_config, "publication_mode", policy.publication_mode
            )
            policy.validation_threshold = getattr(
                request_config, "validation_threshold", policy.validation_threshold
            )
            policy.max_research_items = getattr(
                request_config, "max_research_items", policy.max_research_items
            )

    if overrides and isinstance(overrides, dict):
        if "max_topics" in overrides and overrides["max_topics"] is not None:
            policy.max_topics = overrides["max_topics"]
        if "editorial_threshold" in overrides and overrides["editorial_threshold"] is not None:
            policy.editorial_threshold = overrides["editorial_threshold"]
        if "enable_dry_run_publication" in overrides and overrides["enable_dry_run_publication"] is not None:
            policy.enable_dry_run_publication = overrides["enable_dry_run_publication"]
        if "publication_mode" in overrides and overrides["publication_mode"] is not None:
            policy.publication_mode = overrides["publication_mode"]
        if "validation_threshold" in overrides and overrides["validation_threshold"] is not None:
            policy.validation_threshold = overrides["validation_threshold"]
        if "max_research_items" in overrides and overrides["max_research_items"] is not None:
            policy.max_research_items = overrides["max_research_items"]

    return policy.validate()
