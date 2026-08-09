import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Union

from app.db.database import get_connection
from app.repositories.agent_repository import SQLiteAgentRepository, get_agent_repository


@dataclass
class AgentPersonaData:
    agent_id: str
    persona_name: str
    primary_domain: str
    persona_description: Optional[str] = None
    secondary_domains: List[str] = field(default_factory=list)
    preferred_categories: List[str] = field(default_factory=list)
    excluded_categories: List[str] = field(default_factory=list)
    preferred_keywords: List[str] = field(default_factory=list)
    excluded_keywords: List[str] = field(default_factory=list)
    audience_description: Optional[str] = None
    style_tone: Optional[str] = None
    min_relevance_threshold: float = 0.5
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "persona_name": self.persona_name,
            "persona_description": self.persona_description,
            "primary_domain": self.primary_domain,
            "secondary_domains": self.secondary_domains,
            "preferred_categories": self.preferred_categories,
            "excluded_categories": self.excluded_categories,
            "preferred_keywords": self.preferred_keywords,
            "excluded_keywords": self.excluded_keywords,
            "audience_description": self.audience_description,
            "style_tone": self.style_tone,
            "min_relevance_threshold": self.min_relevance_threshold,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class BasePersonaRepository(ABC):
    @abstractmethod
    def save_persona(self, persona: AgentPersonaData) -> AgentPersonaData:
        """Save or update agent persona configuration."""
        pass

    @abstractmethod
    def get_persona(self, agent_id: str) -> Optional[AgentPersonaData]:
        """Retrieve persona configuration for an agent, falling back to safe defaults for legacy agents."""
        pass

    @abstractmethod
    def delete_persona(self, agent_id: str) -> bool:
        """Reset or delete custom persona configuration for an agent."""
        pass


class SQLitePersonaRepository(BasePersonaRepository):
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path
        self.agent_repo = SQLiteAgentRepository(db_path)

    def save_persona(self, persona: AgentPersonaData) -> AgentPersonaData:
        now_utc = datetime.now(timezone.utc).isoformat()
        created_at = persona.created_at or now_utc

        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO agent_persona (
                        agent_id, persona_name, persona_description, primary_domain,
                        secondary_domains, preferred_categories, excluded_categories,
                        preferred_keywords, excluded_keywords, audience_description,
                        style_tone, min_relevance_threshold, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(agent_id) DO UPDATE SET
                        persona_name = excluded.persona_name,
                        persona_description = excluded.persona_description,
                        primary_domain = excluded.primary_domain,
                        secondary_domains = excluded.secondary_domains,
                        preferred_categories = excluded.preferred_categories,
                        excluded_categories = excluded.excluded_categories,
                        preferred_keywords = excluded.preferred_keywords,
                        excluded_keywords = excluded.excluded_keywords,
                        audience_description = excluded.audience_description,
                        style_tone = excluded.style_tone,
                        min_relevance_threshold = excluded.min_relevance_threshold,
                        updated_at = excluded.updated_at
                    """,
                    (
                        persona.agent_id,
                        persona.persona_name,
                        persona.persona_description,
                        persona.primary_domain,
                        json.dumps(persona.secondary_domains or []),
                        json.dumps(persona.preferred_categories or []),
                        json.dumps(persona.excluded_categories or []),
                        json.dumps(persona.preferred_keywords or []),
                        json.dumps(persona.excluded_keywords or []),
                        persona.audience_description,
                        persona.style_tone,
                        persona.min_relevance_threshold,
                        created_at,
                        now_utc,
                    ),
                )
        finally:
            conn.close()

        persona.created_at = created_at
        persona.updated_at = now_utc
        return persona

    def get_persona(self, agent_id: str) -> Optional[AgentPersonaData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT agent_id, persona_name, persona_description, primary_domain,
                       secondary_domains, preferred_categories, excluded_categories,
                       preferred_keywords, excluded_keywords, audience_description,
                       style_tone, min_relevance_threshold, created_at, updated_at
                FROM agent_persona WHERE agent_id = ?
                """,
                (agent_id,),
            )
            row = cursor.fetchone()
            if row:
                return AgentPersonaData(
                    agent_id=row["agent_id"],
                    persona_name=row["persona_name"],
                    persona_description=row["persona_description"],
                    primary_domain=row["primary_domain"],
                    secondary_domains=json.loads(row["secondary_domains"] or "[]"),
                    preferred_categories=json.loads(row["preferred_categories"] or "[]"),
                    excluded_categories=json.loads(row["excluded_categories"] or "[]"),
                    preferred_keywords=json.loads(row["preferred_keywords"] or "[]"),
                    excluded_keywords=json.loads(row["excluded_keywords"] or "[]"),
                    audience_description=row["audience_description"],
                    style_tone=row["style_tone"],
                    min_relevance_threshold=row["min_relevance_threshold"] if row["min_relevance_threshold"] is not None else 0.5,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        finally:
            conn.close()

        # Fallback to base Agent record for legacy compatibility
        agent = self.agent_repo.get_agent(agent_id)
        if not agent:
            return None

        now_utc = datetime.now(timezone.utc).isoformat()
        return AgentPersonaData(
            agent_id=agent.agent_id,
            persona_name=agent.name,
            primary_domain=agent.domain,
            persona_description=f"Autonomous AI Persona for {agent.name}",
            min_relevance_threshold=0.5,
            created_at=agent.initialized_at or now_utc,
            updated_at=now_utc,
        )

    def delete_persona(self, agent_id: str) -> bool:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM agent_persona WHERE agent_id = ?",
                    (agent_id,),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()


def get_persona_repository() -> BasePersonaRepository:
    """FastAPI dependency provider for PersonaRepository."""
    return SQLitePersonaRepository()
