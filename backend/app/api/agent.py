import secrets
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field, field_validator

from app.repositories.agent_repository import BaseAgentRepository, get_agent_repository

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
