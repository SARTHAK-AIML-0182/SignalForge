from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.workflow.policy import WorkflowPolicy


class WorkflowStatus:
    RUNNING = "RUNNING"
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


# WorkflowConfig is alias to WorkflowPolicy for backwards compatibility
WorkflowConfig = WorkflowPolicy


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
    policy: Optional[Dict[str, Any]] = None
    governance: Optional[Dict[str, Any]] = None
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
