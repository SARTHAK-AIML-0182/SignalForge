import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agent", tags=["Agent"])


class InitResponse(BaseModel):
    agentId: str = Field(..., description="Unique identifier for the initialized agent session")
    status: str = Field(default="initialized", description="Initialization status string")
    message: str = Field(default="Agent initialized successfully (placeholder)", description="Status description")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of initialization")


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


@router.post("/init", response_model=InitResponse)
def init_agent():
    """
    Initialize the autonomous agent session.
    Called exactly once by the evaluator at session start.
    Returns an agentId to query feed updates.
    """
    agent_id = f"agent-{uuid.uuid4().hex[:12]}"
    now_utc = datetime.now(timezone.utc).isoformat()
    return InitResponse(
        agentId=agent_id,
        status="initialized",
        message="Agent initialized successfully (placeholder)",
        timestamp=now_utc,
    )


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
