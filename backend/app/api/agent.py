import secrets
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from app.api.workflow_schemas import (
    WorkflowListResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowStageResponse,
    WorkflowSummaryResponse,
)
from app.repositories import (
    BaseAgentRepository,
    BaseWorkflowRepository,
    get_agent_repository,
    get_workflow_repository,
)
from app.services.workflow import WorkflowConfig, run_agent_workflow

router = APIRouter(prefix="/agent", tags=["Agent"])


class PersonaSchema(BaseModel):
    name: str = Field(..., description="Persona name")
    domain: str = Field(..., description="Persona domain focus")

    @field_validator("name", "domain", mode="before")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Field must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        return stripped


class InitRequest(BaseModel):
    persona: PersonaSchema


class InitResponse(BaseModel):
    agentId: str = Field(..., description="Cryptographically safe unique agent identifier")


class FeedItem(BaseModel):
    id: str = Field(..., description="Unique post ID")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post body content")
    publishedAt: str = Field(..., description="ISO 8601 UTC timestamp of publication")
    sources: List[str] = Field(default_factory=list, description="Source URLs or identifiers")
    rationale: Optional[str] = Field(default=None, description="Editorial publishing rationale")


class FeedResponse(BaseModel):
    agentId: str = Field(..., description="Agent ID for the feed")
    posts: List[FeedItem] = Field(default_factory=list, description="List of published posts")
    status: str = Field(default="ok", description="Response status")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of feed request")


@router.post("/init", response_model=InitResponse, status_code=status.HTTP_200_OK)
def init_agent(
    payload: InitRequest,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository)
):
    """
    Initialize the autonomous agent session.
    Validates persona, generates a cryptographically safe agentId, and persists agent state.
    """
    agent_id = f"agent-{secrets.token_hex(16)}"
    agent_repo.save_agent(
        agent_id=agent_id,
        name=payload.persona.name,
        domain=payload.persona.domain,
    )
    return InitResponse(agentId=agent_id)


@router.get("/feed", response_model=FeedResponse)
def get_feed(agentId: str = Query(..., description="Agent ID received during initialization")):
    """
    Retrieve published posts for the given agentId.
    Polled repeatedly by the evaluator over ~48 hours.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    return FeedResponse(
        agentId=agentId,
        posts=[],
        status="ok",
        timestamp=now_utc,
    )


@router.post("/{agent_id}/workflow/run", response_model=WorkflowRunResponse, status_code=status.HTTP_200_OK)
def run_workflow_endpoint(
    agent_id: str,
    payload: Optional[WorkflowRunRequest] = None,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    workflow_repo: BaseWorkflowRepository = Depends(get_workflow_repository),
):
    """
    Execute the 9-stage autonomous workflow for the specified agent.
    Validates agent existence, runs orchestration, and returns structured workflow result.
    """
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    if payload is None:
        payload = WorkflowRunRequest()

    config_editorial_threshold = (
        payload.editorial_threshold * 10.0
        if payload.editorial_threshold <= 1.0
        else payload.editorial_threshold
    )

    config = WorkflowConfig(
        max_topics=payload.max_topics,
        editorial_threshold=config_editorial_threshold,
        enable_dry_run_publication=payload.enable_dry_run_publication,
    )

    try:
        wf_result = run_agent_workflow(
            agent_id=agent_id,
            config=config,
            agent_repo=agent_repo,
            workflow_repo=workflow_repo,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal workflow execution error."
        ) from None

    stage_responses = [
        WorkflowStageResponse(
            stage_name=st.stage_name,
            status=st.status,
            started_at=st.started_at,
            completed_at=st.completed_at,
            is_successful=st.is_successful,
            rationale=st.rationale,
            entity_ids=st.entity_ids,
            metadata=st.metadata,
        )
        for st in wf_result.stages
    ]

    return WorkflowRunResponse(
        workflow_id=wf_result.workflow_id,
        agent_id=wf_result.agent_id,
        status=wf_result.status,
        started_at=wf_result.started_at,
        completed_at=wf_result.completed_at,
        is_successful=wf_result.is_successful,
        halted_at_stage=wf_result.halted_at_stage,
        rationale=wf_result.rationale,
        selected_topic_ids=wf_result.selected_topic_ids,
        research_ids=wf_result.research_ids,
        draft_ids=wf_result.draft_ids,
        publication_ids=wf_result.publication_ids,
        stages=stage_responses,
        traceability=wf_result.traceability,
    )


@router.get("/{agent_id}/workflow/{workflow_id}", response_model=WorkflowRunResponse, status_code=status.HTTP_200_OK)
def get_workflow_status_endpoint(
    agent_id: str,
    workflow_id: str,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    workflow_repo: BaseWorkflowRepository = Depends(get_workflow_repository),
):
    """
    Retrieve details for a specific workflow execution run by ID.
    Returns HTTP 404 if agent or workflow does not exist, or if workflow belongs to another agent.
    """
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    wf_result = workflow_repo.get_workflow(workflow_id)
    if not wf_result or wf_result.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found for agent '{agent_id}'."
        )

    stage_responses = [
        WorkflowStageResponse(
            stage_name=st.stage_name,
            status=st.status,
            started_at=st.started_at,
            completed_at=st.completed_at,
            is_successful=st.is_successful,
            rationale=st.rationale,
            entity_ids=st.entity_ids,
            metadata=st.metadata,
        )
        for st in wf_result.stages
    ]

    return WorkflowRunResponse(
        workflow_id=wf_result.workflow_id,
        agent_id=wf_result.agent_id,
        status=wf_result.status,
        started_at=wf_result.started_at,
        completed_at=wf_result.completed_at,
        is_successful=wf_result.is_successful,
        halted_at_stage=wf_result.halted_at_stage,
        rationale=wf_result.rationale,
        selected_topic_ids=wf_result.selected_topic_ids,
        research_ids=wf_result.research_ids,
        draft_ids=wf_result.draft_ids,
        publication_ids=wf_result.publication_ids,
        stages=stage_responses,
        traceability=wf_result.traceability,
    )


@router.get("/{agent_id}/workflows", response_model=WorkflowListResponse, status_code=status.HTTP_200_OK)
def list_workflows_endpoint(
    agent_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of historical workflows to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    workflow_repo: BaseWorkflowRepository = Depends(get_workflow_repository),
):
    """
    Retrieve a paginated list of historical workflow execution summaries for an agent.
    Returns HTTP 404 if agent is not found.
    """
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    workflows = workflow_repo.list_workflows_by_agent(agent_id=agent_id, limit=limit, offset=offset)
    total = workflow_repo.count_workflows_by_agent(agent_id=agent_id)

    summaries = [
        WorkflowSummaryResponse(
            workflow_id=wf.workflow_id,
            agent_id=wf.agent_id,
            status=wf.status,
            started_at=wf.started_at,
            completed_at=wf.completed_at,
            is_successful=wf.is_successful,
            rationale=wf.rationale,
            selected_topic_ids_count=len(wf.selected_topic_ids),
            publication_ids_count=len(wf.publication_ids),
        )
        for wf in workflows
    ]

    return WorkflowListResponse(
        items=summaries,
        total=total,
        limit=limit,
        offset=offset,
    )

