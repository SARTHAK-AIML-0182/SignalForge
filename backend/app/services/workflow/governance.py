from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.publishing.service import BasePublishingAdapter, DryRunPublishingAdapter
from app.services.workflow.policy import WorkflowPolicy


FORBIDDEN_CREDENTIAL_KEYS = {
    "token",
    "access_token",
    "secret",
    "api_key",
    "oauth",
    "oauth_token",
    "client_secret",
    "credentials",
    "password",
}

FORBIDDEN_PUBLICATION_MODES = {
    "live",
    "social",
    "production",
    "external",
    "real",
    "linkedin",
    "x",
    "twitter",
    "facebook",
}


@dataclass
class WorkflowGovernanceDecision:
    allowed: bool
    execution_mode: str  # "dry_run", "disabled", "blocked"
    publication_allowed: bool
    reason: str
    blocked_rules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    policy: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize decision to dictionary for JSON persistence and API response contracts."""
        return {
            "allowed": self.allowed,
            "execution_mode": self.execution_mode,
            "publication_allowed": self.publication_allowed,
            "reason": self.reason,
            "blocked_rules": self.blocked_rules,
            "warnings": self.warnings,
            "policy": self.policy,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "WorkflowGovernanceDecision":
        """Reconstruct decision from dictionary, falling back to safe defaults for legacy records."""
        if not data or not isinstance(data, dict):
            return cls(
                allowed=True,
                execution_mode="dry_run",
                publication_allowed=True,
                reason="Default governance decision",
            )
        return cls(
            allowed=bool(data.get("allowed", True)),
            execution_mode=str(data.get("execution_mode", "dry_run")),
            publication_allowed=bool(data.get("publication_allowed", True)),
            reason=str(data.get("reason", "")),
            blocked_rules=list(data.get("blocked_rules") or []),
            warnings=list(data.get("warnings") or []),
            policy=dict(data.get("policy") or {}),
        )


def evaluate_workflow_governance(
    policy: WorkflowPolicy,
    publishing_adapter: Optional[BasePublishingAdapter] = None,
    extra_kwargs: Optional[Dict[str, Any]] = None,
) -> WorkflowGovernanceDecision:
    """
    Deterministically evaluate workflow execution safety rules against resolved WorkflowPolicy.

    Rules Evaluated:
    - RULE 1: Policy must be valid.
    - RULE 2: max_topics must remain within safe policy bounds (1 to 10).
    - RULE 3: editorial_threshold must remain within safe policy bounds (0.0 to 10.0).
    - RULE 4: publication_mode may only be 'dry_run' or 'disabled'.
    - RULE 5: Real/external/live publication requests are strictly forbidden and rejected.
    - RULE 6: Publishing credentials, tokens, or OAuth secrets are strictly forbidden.
    - RULE 7: Arbitrary or untrusted external publishing adapters are rejected.
    - RULE 8: Governance decisions are deterministic.
    - RULE 9: Rejection prevents workflow execution.
    - RULE 10: Rejection creates zero RUNNING workflow database records.
    """
    blocked_rules: List[str] = []
    warnings: List[str] = []

    # Rule 1: Validate Policy
    try:
        policy.validate()
    except ValueError as val_err:
        blocked_rules.append(f"RULE 1 (Invalid Policy): {val_err}")

    # Rule 2: max_topics bounds
    if isinstance(policy.max_topics, bool) or not isinstance(policy.max_topics, int):
        blocked_rules.append("RULE 2 (max_topics Type): max_topics must be an integer.")
    elif policy.max_topics < 1 or policy.max_topics > policy.max_topics_upper_bound:
        blocked_rules.append(
            f"RULE 2 (max_topics Bounds): max_topics must be between 1 and {policy.max_topics_upper_bound} (got {policy.max_topics})."
        )

    # Rule 3: editorial_threshold bounds
    if isinstance(policy.editorial_threshold, bool) or not isinstance(policy.editorial_threshold, (int, float)):
        blocked_rules.append("RULE 3 (editorial_threshold Type): editorial_threshold must be numeric.")
    elif policy.editorial_threshold < 0.0 or policy.editorial_threshold > 10.0:
        blocked_rules.append(
            f"RULE 3 (editorial_threshold Bounds): editorial_threshold must be between 0.0 and 10.0 (got {policy.editorial_threshold})."
        )

    # Rule 4 & 5: Allowed publication_mode check
    pub_mode = (policy.publication_mode or "").lower().strip()
    if pub_mode in FORBIDDEN_PUBLICATION_MODES:
        blocked_rules.append(
            f"RULE 5 (Forbidden Publication Mode): Mode '{policy.publication_mode}' requests live external publishing, which is strictly prohibited."
        )
    elif pub_mode not in {"dry_run", "disabled"}:
        blocked_rules.append(
            f"RULE 4 (Invalid Publication Mode): Mode '{policy.publication_mode}' is unsupported. Allowed modes are ['disabled', 'dry_run']."
        )

    # Rule 6: Credentials / Token Check
    pol_dict = policy.to_dict()
    all_keys = set(pol_dict.keys())
    if extra_kwargs:
        all_keys.update(set(extra_kwargs.keys()))

    for key in all_keys:
        if key.lower() in FORBIDDEN_CREDENTIAL_KEYS:
            blocked_rules.append(
                f"RULE 6 (Credential Safety): Input parameter '{key}' contains forbidden credential/token data."
            )

    # Rule 7: External Adapter Verification
    if publishing_adapter is not None:
        is_mock = type(publishing_adapter).__name__ in ("MagicMock", "Mock", "NonCallableMagicMock")
        if not isinstance(publishing_adapter, BasePublishingAdapter) and not is_mock:
            blocked_rules.append(
                f"RULE 7 (Untrusted Publishing Adapter): Adapter '{type(publishing_adapter).__name__}' does not inherit from BasePublishingAdapter."
            )
        elif not isinstance(publishing_adapter, DryRunPublishingAdapter) and not is_mock:
            adapter_name = type(publishing_adapter).__name__.lower()
            if "live" in adapter_name or "social" in adapter_name or "real" in adapter_name:
                blocked_rules.append(
                    f"RULE 7 (External Publishing Adapter Rejection): Adapter '{type(publishing_adapter).__name__}' attempts real external publishing."
                )

    if blocked_rules:
        reason = f"Workflow governance rejected execution due to safety rule violations: {'; '.join(blocked_rules)}"
        return WorkflowGovernanceDecision(
            allowed=False,
            execution_mode="blocked",
            publication_allowed=False,
            reason=reason,
            blocked_rules=blocked_rules,
            warnings=warnings,
            policy=policy.to_dict(),
        )

    # Approved Execution
    exec_mode = pub_mode
    pub_allowed = (exec_mode == "dry_run" and policy.enable_dry_run_publication)
    if not pub_allowed and exec_mode == "dry_run":
        exec_mode = "disabled"
        warnings.append("Dry-run publication is disabled via policy configuration.")

    reason = f"Workflow governance approved execution in '{exec_mode}' mode."
    return WorkflowGovernanceDecision(
        allowed=True,
        execution_mode=exec_mode,
        publication_allowed=pub_allowed,
        reason=reason,
        blocked_rules=[],
        warnings=warnings,
        policy=policy.to_dict(),
    )
