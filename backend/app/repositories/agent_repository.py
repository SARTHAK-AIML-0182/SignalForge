from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Union

from app.db.database import get_connection


@dataclass
class AgentData:
    agent_id: str
    name: str
    domain: str
    status: str = "active"
    initialized_at: Optional[str] = None

    @property
    def persona_name(self) -> str:
        return self.name

    @property
    def persona_domain(self) -> str:
        return self.domain

    @property
    def created_at(self) -> str:
        return self.initialized_at or ""


class BaseAgentRepository(ABC):
    @abstractmethod
    def save_agent(self, agent_id: str, name: str, domain: str, status: str = "active") -> AgentData:
        """Save initialized agent state."""
        pass

    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[AgentData]:
        """Retrieve agent state by ID."""
        pass


class InMemoryAgentRepository(BaseAgentRepository):
    def __init__(self):
        self._store: Dict[str, AgentData] = {}

    def save_agent(self, agent_id: str, name: str, domain: str, status: str = "active") -> AgentData:
        now_utc = datetime.now(timezone.utc).isoformat()
        agent = AgentData(
            agent_id=agent_id,
            name=name,
            domain=domain,
            status=status,
            initialized_at=now_utc
        )
        self._store[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[AgentData]:
        return self._store.get(agent_id)


class SQLiteAgentRepository(BaseAgentRepository):
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path

    def save_agent(self, agent_id: str, name: str, domain: str, status: str = "active") -> AgentData:
        now_utc = datetime.now(timezone.utc).isoformat()
        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO agents (agent_id, persona_name, persona_domain, status, initialized_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(agent_id) DO UPDATE SET
                        persona_name=excluded.persona_name,
                        persona_domain=excluded.persona_domain,
                        status=excluded.status
                    """,
                    (agent_id, name, domain, status, now_utc)
                )
        finally:
            conn.close()

        return AgentData(
            agent_id=agent_id,
            name=name,
            domain=domain,
            status=status,
            initialized_at=now_utc
        )

    def get_agent(self, agent_id: str) -> Optional[AgentData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT agent_id, persona_name, persona_domain, status, initialized_at FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return AgentData(
                agent_id=row["agent_id"],
                name=row["persona_name"],
                domain=row["persona_domain"],
                status=row["status"],
                initialized_at=row["initialized_at"]
            )
        finally:
            conn.close()


def get_agent_repository() -> BaseAgentRepository:
    """Dependency provider for AgentRepository."""
    return SQLiteAgentRepository()
