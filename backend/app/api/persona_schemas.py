from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class PersonaUpdateRequest(BaseModel):
    persona_name: str = Field(..., description="Persona name")
    primary_domain: str = Field(..., description="Primary domain focus")
    persona_description: Optional[str] = Field(default=None, max_length=500, description="Persona description")
    secondary_domains: List[str] = Field(default_factory=list, max_length=50, description="Secondary domains")
    preferred_categories: List[str] = Field(default_factory=list, max_length=50, description="Preferred content categories")
    excluded_categories: List[str] = Field(default_factory=list, max_length=50, description="Excluded content categories")
    preferred_keywords: List[str] = Field(default_factory=list, max_length=50, description="Preferred keywords")
    excluded_keywords: List[str] = Field(default_factory=list, max_length=50, description="Excluded keywords")
    audience_description: Optional[str] = Field(default=None, max_length=500, description="Audience description")
    style_tone: Optional[str] = Field(default=None, max_length=500, description="Editorial style and tone")
    min_relevance_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum relevance threshold (0.0 to 1.0)")

    @field_validator("persona_name", "primary_domain", mode="before")
    @classmethod
    def validate_non_empty(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("Field must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        if len(stripped) > 100:
            raise ValueError("Field length cannot exceed 100 characters")
        return stripped

    @field_validator(
        "secondary_domains",
        "preferred_categories",
        "excluded_categories",
        "preferred_keywords",
        "excluded_keywords",
        mode="before"
    )
    @classmethod
    def validate_str_list(cls, value: Any) -> List[str]:
        if not isinstance(value, list):
            raise ValueError("Field must be a list of strings")
        cleaned = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("List items must be strings")
            s = item.strip()
            if s:
                if len(s) > 100:
                    raise ValueError("List item length cannot exceed 100 characters")
                cleaned.append(s)
        return cleaned


class PersonaResponse(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    persona_name: str = Field(..., description="Persona name")
    persona_description: Optional[str] = Field(default=None, description="Persona description")
    primary_domain: str = Field(..., description="Primary domain focus")
    secondary_domains: List[str] = Field(default_factory=list, description="Secondary domains")
    preferred_categories: List[str] = Field(default_factory=list, description="Preferred categories")
    excluded_categories: List[str] = Field(default_factory=list, description="Excluded categories")
    preferred_keywords: List[str] = Field(default_factory=list, description="Preferred keywords")
    excluded_keywords: List[str] = Field(default_factory=list, description="Excluded keywords")
    audience_description: Optional[str] = Field(default=None, description="Audience description")
    style_tone: Optional[str] = Field(default=None, description="Editorial style and tone")
    min_relevance_threshold: float = Field(0.5, description="Minimum relevance threshold")
    created_at: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp")
    updated_at: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp")


class FeedConfigUpdateRequest(BaseModel):
    max_topics: int = Field(default=5, ge=1, le=10, description="Maximum topics per workflow execution")
    min_relevance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum relevance score threshold")
    allowed_categories: List[str] = Field(default_factory=list, max_length=50, description="Allowed categories")
    excluded_categories: List[str] = Field(default_factory=list, max_length=50, description="Excluded categories")
    preferred_keywords: List[str] = Field(default_factory=list, max_length=50, description="Preferred keywords")
    excluded_keywords: List[str] = Field(default_factory=list, max_length=50, description="Excluded keywords")

    @field_validator(
        "allowed_categories",
        "excluded_categories",
        "preferred_keywords",
        "excluded_keywords",
        mode="before"
    )
    @classmethod
    def validate_str_list(cls, value: Any) -> List[str]:
        if not isinstance(value, list):
            raise ValueError("Field must be a list of strings")
        cleaned = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("List items must be strings")
            s = item.strip()
            if s:
                if len(s) > 100:
                    raise ValueError("List item length cannot exceed 100 characters")
                cleaned.append(s)
        return cleaned


class FeedConfigResponse(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    max_topics: int = Field(..., description="Maximum topics per workflow execution")
    min_relevance_score: float = Field(..., description="Minimum relevance score threshold")
    allowed_categories: List[str] = Field(default_factory=list, description="Allowed categories")
    excluded_categories: List[str] = Field(default_factory=list, description="Excluded categories")
    preferred_keywords: List[str] = Field(default_factory=list, description="Preferred keywords")
    excluded_keywords: List[str] = Field(default_factory=list, description="Excluded keywords")
