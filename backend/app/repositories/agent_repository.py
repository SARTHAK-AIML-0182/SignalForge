from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class AgentData:
    agent_id: str
    name: str
    domain: str
    created_at: datetime


class BaseAgentRepository(ABC):
    @abstractmethod
    def save_agent(self, agent_id: str, name: str, domain: str) -> AgentData:
        """Save initialized agent state."""
        pass

    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[AgentData]:
        """Retrieve agent state by ID."""
        pass


class InMemoryAgentRepository(BaseAgentRepository):
    def __init__(self):
        self._store: Dict[str, AgentData] = {}

    def save_agent(self, agent_id: str, name: str, domain: str) -> AgentData:
        agent = AgentData(
            agent_id=agent_id,
            name=name,
            domain=domain,
            created_at=datetime.now(timezone.utc)
        )
        self._store[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[AgentData]:
        return self._store.get(agent_id)


# Global singleton instance for in-memory persistence
_agent_repository_instance = InMemoryAgentRepository()


def get_agent_repository() -> BaseAgentRepository:
    """Dependency provider for AgentRepository."""
    return _agent_repository_instance
