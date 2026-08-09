from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class WorkflowStatus:
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    NO_CONTENT = "NO_CONTENT"
    FAILED = "FAILED"


class WorkflowStageStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


@dataclass
class WorkflowConfig:
    max_topics: int = 5
    max_research_items: int = 3
    enable_dry_run_publication: bool = True
    validation_threshold: float = 0.65
    editorial_threshold: float = 6.5


@dataclass
class WorkflowStageResult:
    stage_name: str
    status: str  # PENDING, RUNNING, SUCCEEDED, FAILED, SKIPPED, BLOCKED
    started_at: str
    completed_at: str
    is_successful: bool
    rationale: str
    entity_ids: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentWorkflowResult:
    workflow_id: str
    agent_id: str
    status: str  # SUCCESS, PARTIAL_SUCCESS, NO_CONTENT, FAILED
    started_at: str
    completed_at: str
    stages: List[WorkflowStageResult]
    selected_topic_ids: List[str]
    research_ids: List[str]
    draft_ids: List[str]
    publication_ids: List[str]
    is_successful: bool
    halted_at_stage: Optional[str]
    rationale: str
    traceability: Dict[str, Any] = field(default_factory=dict)
