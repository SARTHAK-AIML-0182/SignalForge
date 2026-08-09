import secrets
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator

from app.api.persona_schemas import (
    FeedConfigResponse,
    FeedConfigUpdateRequest,
    PersonaResponse,
    PersonaUpdateRequest,
)
from app.api.validators import (
    validate_identifier,
    validate_pagination,
    validate_status_filter,
)
from app.api.workflow_schemas import (
    WorkflowInspectionResponse,
    WorkflowListResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowStageResponse,
    WorkflowStageStats,
    WorkflowSummaryResponse,
)
from app.core.rate_limiter import (
    rate_limit_feed_config_update,
    rate_limit_persona_update,
    rate_limit_workflow_run,
)
from app.repositories import (
    AgentPersonaData,
    BaseAgentRepository,
    BasePersonaRepository,
    BasePostRepository,
    BaseWorkflowRepository,
    get_agent_repository,
    get_persona_repository,
    get_post_repository,
    get_workflow_repository,
)
from app.repositories.workflow_repository import (
    calculate_duration_seconds,
    calculate_stage_stats,
    extract_traceability_summary,
)
from app.services.workflow import WorkflowConfig, run_agent_workflow

router = APIRouter(prefix="/agent", tags=["Agent"])


class PersonaSchema(BaseModel):
    name: str = Field(..., max_length=100, description="Persona name")
    domain: str = Field(..., max_length=100, description="Persona domain focus")

    @field_validator("name", "domain", mode="before")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Field must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        if len(stripped) > 100:
            raise ValueError("Field length cannot exceed 100 characters")
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
def get_feed(
    agentId: str = Query(..., description="Agent ID received during initialization"),
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    post_repo: BasePostRepository = Depends(get_post_repository),
):
    """
    Retrieve published posts for the given agentId.
    Polled repeatedly by the evaluator over ~48 hours.
    Returns HTTP 404 if agent is not found.
    """
    agentId = validate_identifier(agentId, "agentId")
    agent = agent_repo.get_agent(agentId)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agentId}' not found."
        )

    posts_data = post_repo.list_posts_by_agent(agentId)
    feed_items = [
        FeedItem(
            id=p.post_id,
            title=f"Post for topic {p.topic_id}" if p.topic_id else "Published Post",
            content=p.text,
            publishedAt=p.created_at or datetime.now(timezone.utc).isoformat(),
            sources=[str(s) for s in (p.sources or [])],
            rationale=p.rationale,
        )
        for p in posts_data
    ]

    now_utc = datetime.now(timezone.utc).isoformat()
    return FeedResponse(
        agentId=agentId,
        posts=feed_items,
        status="ok",
        timestamp=now_utc,
    )


@router.post("/{agent_id}/workflow/run", response_model=WorkflowRunResponse, status_code=status.HTTP_200_OK)
def run_workflow_endpoint(
    agent_id: str,
    request: Request,
    payload: Optional[WorkflowRunRequest] = None,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    workflow_repo: BaseWorkflowRepository = Depends(get_workflow_repository),
):
    """
    Execute the 9-stage autonomous workflow for the specified agent.
    Validates agent existence, enforces process-local rate limiting, runs orchestration, and returns structured workflow result.
    """
    agent_id = validate_identifier(agent_id, "agent_id")
    rate_limit_workflow_run(agent_id, request)

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
        publication_mode=payload.publication_mode or "dry_run",
    )

    try:
        wf_result = run_agent_workflow(
            agent_id=agent_id,
            config=config,
            agent_repo=agent_repo,
            workflow_repo=workflow_repo,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )
    except HTTPException:
        raise
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
        policy=wf_result.policy,
        governance=wf_result.governance,
        diagnostics=getattr(wf_result, "diagnostics", []) or wf_result.traceability.get("diagnostics", []),
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
    agent_id = validate_identifier(agent_id, "agent_id")
    workflow_id = validate_identifier(workflow_id, "workflow_id")

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
        policy=wf_result.policy,
        governance=wf_result.governance,
        diagnostics=getattr(wf_result, "diagnostics", []) or wf_result.traceability.get("diagnostics", []),
    )


@router.get("/{agent_id}/workflow/{workflow_id}/inspection", response_model=WorkflowInspectionResponse, status_code=status.HTTP_200_OK)
def inspect_workflow_endpoint(
    agent_id: str,
    workflow_id: str,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    workflow_repo: BaseWorkflowRepository = Depends(get_workflow_repository),
):
    """
    Retrieve inspection-oriented observability breakdown for a specific workflow run.
    Includes stage statistics, execution duration, entity counts, halted stage, rationale, and concise traceability summary.
    Returns HTTP 404 if agent or workflow is not found or if workflow belongs to another agent.
    """
    agent_id = validate_identifier(agent_id, "agent_id")
    workflow_id = validate_identifier(workflow_id, "workflow_id")

    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    wf = workflow_repo.get_workflow(workflow_id)
    if not wf or wf.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found for agent '{agent_id}'."
        )

    duration = calculate_duration_seconds(wf.started_at, wf.completed_at)
    stats_dict = calculate_stage_stats(wf.stages)
    trace_summary = extract_traceability_summary(wf.traceability)

    stage_stats = WorkflowStageStats(
        total_stages=stats_dict["total_stages"],
        succeeded_stages=stats_dict["succeeded_stages"],
        failed_stages=stats_dict["failed_stages"],
        blocked_stages=stats_dict["blocked_stages"],
        skipped_stages=stats_dict["skipped_stages"],
        running_stages=stats_dict["running_stages"],
    )

    return WorkflowInspectionResponse(
        workflow_id=wf.workflow_id,
        agent_id=wf.agent_id,
        status=wf.status,
        started_at=wf.started_at,
        completed_at=wf.completed_at,
        duration_seconds=duration,
        is_successful=wf.is_successful,
        halted_at_stage=wf.halted_at_stage,
        rationale=wf.rationale,
        stage_stats=stage_stats,
        selected_topic_count=len(wf.selected_topic_ids or []),
        research_count=len(wf.research_ids or []),
        draft_count=len(wf.draft_ids or []),
        publication_count=len(wf.publication_ids or []),
        traceability_summary=trace_summary,
        policy=wf.policy,
        governance=wf.governance,
        diagnostics=getattr(wf, "diagnostics", []) or wf.traceability.get("diagnostics", []),
    )


@router.get("/{agent_id}/workflows", response_model=WorkflowListResponse, status_code=status.HTTP_200_OK)
def list_workflows_endpoint(
    agent_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by workflow status (e.g. SUCCESS, FAILED, NO_CONTENT)"),
    successful: Optional[bool] = Query(default=None, alias="successful", description="Filter by overall success boolean (true/false)"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of historical workflows to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    workflow_repo: BaseWorkflowRepository = Depends(get_workflow_repository),
):
    """
    Retrieve a paginated list of historical workflow execution summaries for an agent with optional status/success filters.
    Returns HTTP 404 if agent is not found.
    """
    agent_id = validate_identifier(agent_id, "agent_id")
    status_filter = validate_status_filter(status_filter)
    validate_pagination(limit, offset)

    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    workflows = workflow_repo.list_workflows_by_agent(
        agent_id=agent_id,
        status=status_filter,
        is_successful=successful,
        limit=limit,
        offset=offset,
    )
    total = workflow_repo.count_workflows_by_agent(
        agent_id=agent_id,
        status=status_filter,
        is_successful=successful,
    )

    summaries = [
        WorkflowSummaryResponse(
            workflow_id=wf.workflow_id,
            agent_id=wf.agent_id,
            status=wf.status,
            started_at=wf.started_at,
            completed_at=wf.completed_at,
            duration_seconds=calculate_duration_seconds(wf.started_at, wf.completed_at),
            is_successful=wf.is_successful,
            rationale=wf.rationale,
            selected_topic_count=len(wf.selected_topic_ids or []),
            selected_topic_ids_count=len(wf.selected_topic_ids or []),
            research_count=len(wf.research_ids or []),
            draft_count=len(wf.draft_ids or []),
            publication_count=len(wf.publication_ids or []),
            publication_ids_count=len(wf.publication_ids or []),
            policy=wf.policy,
            governance=wf.governance,
            diagnostics=getattr(wf, "diagnostics", []) or wf.traceability.get("diagnostics", []),
        )
        for wf in workflows
    ]

    return WorkflowListResponse(
        items=summaries,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{agent_id}/persona", response_model=PersonaResponse, status_code=status.HTTP_200_OK)
def get_persona_endpoint(
    agent_id: str,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    persona_repo: BasePersonaRepository = Depends(get_persona_repository),
):
    """
    Retrieve persona configuration for a specific agent.
    Returns HTTP 404 if agent is not found.
    """
    agent_id = validate_identifier(agent_id, "agent_id")
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    persona = persona_repo.get_persona(agent_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona configuration for agent '{agent_id}' not found."
        )

    return PersonaResponse(**persona.to_dict())


@router.put("/{agent_id}/persona", response_model=PersonaResponse, status_code=status.HTTP_200_OK)
def update_persona_endpoint(
    agent_id: str,
    request: Request,
    payload: PersonaUpdateRequest,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    persona_repo: BasePersonaRepository = Depends(get_persona_repository),
):
    """
    Create or update custom persona configuration for an agent.
    Enforces process-local rate limiting, validates input parameters, and returns stored persona configuration.
    """
    agent_id = validate_identifier(agent_id, "agent_id")
    rate_limit_persona_update(agent_id, request)

    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    existing = persona_repo.get_persona(agent_id)
    created_at = existing.created_at if existing else None

    persona_data = AgentPersonaData(
        agent_id=agent_id,
        persona_name=payload.persona_name,
        primary_domain=payload.primary_domain,
        persona_description=payload.persona_description,
        secondary_domains=payload.secondary_domains,
        preferred_categories=payload.preferred_categories,
        excluded_categories=payload.excluded_categories,
        preferred_keywords=payload.preferred_keywords,
        excluded_keywords=payload.excluded_keywords,
        audience_description=payload.audience_description,
        style_tone=payload.style_tone,
        min_relevance_threshold=payload.min_relevance_threshold,
        created_at=created_at,
    )

    saved = persona_repo.save_persona(persona_data)
    return PersonaResponse(**saved.to_dict())


@router.get("/{agent_id}/feed/config", response_model=FeedConfigResponse, status_code=status.HTTP_200_OK)
def get_feed_config_endpoint(
    agent_id: str,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    persona_repo: BasePersonaRepository = Depends(get_persona_repository),
):
    """
    Retrieve feed generation configuration for an agent.
    Returns HTTP 404 if agent is not found.
    """
    agent_id = validate_identifier(agent_id, "agent_id")
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    persona = persona_repo.get_persona(agent_id)
    return FeedConfigResponse(
        agent_id=agent_id,
        max_topics=5,
        min_relevance_score=persona.min_relevance_threshold if persona else 0.5,
        allowed_categories=persona.preferred_categories if persona else [],
        excluded_categories=persona.excluded_categories if persona else [],
        preferred_keywords=persona.preferred_keywords if persona else [],
        excluded_keywords=persona.excluded_keywords if persona else [],
    )


@router.put("/{agent_id}/feed/config", response_model=FeedConfigResponse, status_code=status.HTTP_200_OK)
def update_feed_config_endpoint(
    agent_id: str,
    request: Request,
    payload: FeedConfigUpdateRequest,
    agent_repo: BaseAgentRepository = Depends(get_agent_repository),
    persona_repo: BasePersonaRepository = Depends(get_persona_repository),
):
    """
    Update feed configuration rules for an agent.
    Enforces process-local rate limiting and returns stored feed configuration response.
    """
    agent_id = validate_identifier(agent_id, "agent_id")
    rate_limit_feed_config_update(agent_id, request)

    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found."
        )

    persona = persona_repo.get_persona(agent_id)
    if not persona:
        persona = AgentPersonaData(
            agent_id=agent_id,
            persona_name=agent.name,
            primary_domain=agent.domain,
        )

    persona.preferred_categories = payload.allowed_categories
    persona.excluded_categories = payload.excluded_categories
    persona.preferred_keywords = payload.preferred_keywords
    persona.excluded_keywords = payload.excluded_keywords
    persona.min_relevance_threshold = payload.min_relevance_score

    saved = persona_repo.save_persona(persona)
    return FeedConfigResponse(
        agent_id=agent_id,
        max_topics=payload.max_topics,
        min_relevance_score=saved.min_relevance_threshold,
        allowed_categories=saved.preferred_categories,
        excluded_categories=saved.excluded_categories,
        preferred_keywords=saved.preferred_keywords,
        excluded_keywords=saved.excluded_keywords,
    )
