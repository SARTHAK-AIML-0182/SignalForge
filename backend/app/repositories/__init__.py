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
]
