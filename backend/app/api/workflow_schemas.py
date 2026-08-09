from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class WorkflowRunRequest(BaseModel):
    max_topics: int = Field(default=1, ge=1, description="Maximum number of selected topics to process (must be >= 1)")
    editorial_threshold: float = Field(default=0.65, ge=0.0, le=1.0, description="Editorial selection threshold (between 0.0 and 1.0)")
    enable_dry_run_publication: bool = Field(default=True, description="Enable local dry-run publication stage")

    @field_validator("max_topics", mode="before")
    @classmethod
    def validate_max_topics(cls, v: Any) -> Any:
        if isinstance(v, bool):
            raise ValueError("max_topics must be an integer, not a boolean")
        return v

    @field_validator("editorial_threshold", mode="before")
    @classmethod
    def validate_threshold(cls, v: Any) -> Any:
        if isinstance(v, bool):
            raise ValueError("editorial_threshold must be a float, not a boolean")
        return v


class WorkflowStageResponse(BaseModel):
    stage_name: str = Field(..., description="Stage identifier")
    status: str = Field(..., description="Stage execution status")
    started_at: str = Field(..., description="ISO 8601 UTC timestamp when stage started")
    completed_at: str = Field(..., description="ISO 8601 UTC timestamp when stage completed")
    is_successful: bool = Field(..., description="Whether stage completed successfully")
    rationale: str = Field(..., description="Human-readable stage rationale or details")
    entity_ids: Dict[str, Any] = Field(default_factory=dict, description="Relevant entity IDs produced in stage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured stage metadata")


class WorkflowRunResponse(BaseModel):
    workflow_id: str = Field(..., description="Unique workflow execution ID")
    agent_id: str = Field(..., description="Target agent ID")
    status: str = Field(..., description="Overall workflow status (SUCCESS, PARTIAL_SUCCESS, NO_CONTENT, FAILED)")
    started_at: str = Field(..., description="ISO 8601 UTC timestamp when workflow started")
    completed_at: str = Field(..., description="ISO 8601 UTC timestamp when workflow completed")
    is_successful: bool = Field(..., description="Whether overall workflow execution succeeded")
    halted_at_stage: Optional[str] = Field(default=None, description="Stage where workflow halted if failed")
    rationale: str = Field(..., description="Human-readable workflow execution rationale")
    selected_topic_ids: List[str] = Field(default_factory=list, description="IDs of topics selected by editorial engine")
    research_ids: List[str] = Field(default_factory=list, description="IDs of research records generated")
    draft_ids: List[str] = Field(default_factory=list, description="IDs of draft articles generated")
    publication_ids: List[str] = Field(default_factory=list, description="IDs of dry-run publications produced")
    stages: List[WorkflowStageResponse] = Field(default_factory=list, description="Structured stage results")
    traceability: Dict[str, Any] = Field(default_factory=dict, description="9-stage end-to-end traceability mapping")


class WorkflowSummaryResponse(BaseModel):
    workflow_id: str = Field(..., description="Unique workflow execution ID")
    agent_id: str = Field(..., description="Target agent ID")
    status: str = Field(..., description="Overall workflow status")
    started_at: str = Field(..., description="ISO 8601 UTC timestamp when workflow started")
    completed_at: str = Field(..., description="ISO 8601 UTC timestamp when workflow completed")
    is_successful: bool = Field(..., description="Whether workflow execution succeeded")
    rationale: str = Field(..., description="Human-readable workflow execution rationale")
    selected_topic_ids_count: int = Field(0, description="Count of selected topics")
    publication_ids_count: int = Field(0, description="Count of publications produced")


class WorkflowListResponse(BaseModel):
    items: List[WorkflowSummaryResponse] = Field(default_factory=list, description="Historical workflow execution summaries")
    total: int = Field(..., description="Total count of workflows for agent")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")
