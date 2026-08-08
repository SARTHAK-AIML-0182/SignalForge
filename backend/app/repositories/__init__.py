"""Repository package for SignalForge data persistence abstraction."""

from app.repositories.agent_repository import (
    AgentData,
    BaseAgentRepository,
    InMemoryAgentRepository,
    SQLiteAgentRepository,
    get_agent_repository,
)
from app.repositories.topic_repository import (
    TopicData,
    BaseTopicRepository,
    SQLiteTopicRepository,
    get_topic_repository,
)
from app.repositories.post_repository import (
    PostData,
    BasePostRepository,
    SQLitePostRepository,
    get_post_repository,
)
from app.repositories.research_repository import (
    ResearchData,
    BaseResearchRepository,
    SQLiteResearchRepository,
    get_research_repository,
)
from app.repositories.evidence_repository import (
    EvidenceData,
    BaseEvidenceRepository,
    SQLiteEvidenceRepository,
    get_evidence_repository,
)

__all__ = [
    "AgentData",
    "BaseAgentRepository",
    "InMemoryAgentRepository",
    "SQLiteAgentRepository",
    "get_agent_repository",
    "TopicData",
    "BaseTopicRepository",
    "SQLiteTopicRepository",
    "get_topic_repository",
    "PostData",
    "BasePostRepository",
    "SQLitePostRepository",
    "get_post_repository",
    "ResearchData",
    "BaseResearchRepository",
    "SQLiteResearchRepository",
    "get_research_repository",
    "EvidenceData",
    "BaseEvidenceRepository",
    "SQLiteEvidenceRepository",
    "get_evidence_repository",
]
