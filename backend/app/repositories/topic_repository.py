from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from app.db.database import get_connection


@dataclass
class TopicData:
    topic_id: str
    agent_id: str
    title: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    discovered_at: Optional[str] = None
    editorial_score: float = 0.0
    status: str = "discovered"


class BaseTopicRepository(ABC):
    @abstractmethod
    def create_topic(
        self,
        topic_id: str,
        agent_id: str,
        title: str,
        description: Optional[str] = None,
        source_url: Optional[str] = None,
        source_name: Optional[str] = None,
        editorial_score: float = 0.0,
        status: str = "discovered"
    ) -> TopicData:
        """Create a new topic entity."""
        pass

    @abstractmethod
    def get_topic(self, topic_id: str) -> Optional[TopicData]:
        """Retrieve topic by ID."""
        pass

    @abstractmethod
    def list_topics_by_agent(self, agent_id: str) -> List[TopicData]:
        """List all topics for an agent."""
        pass


class SQLiteTopicRepository(BaseTopicRepository):
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path

    def create_topic(
        self,
        topic_id: str,
        agent_id: str,
        title: str,
        description: Optional[str] = None,
        source_url: Optional[str] = None,
        source_name: Optional[str] = None,
        editorial_score: float = 0.0,
        status: str = "discovered"
    ) -> TopicData:
        now_utc = datetime.now(timezone.utc).isoformat()
        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO topics (
                        topic_id, agent_id, title, description, source_url, source_name, discovered_at, editorial_score, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (topic_id, agent_id, title, description, source_url, source_name, now_utc, editorial_score, status)
                )
        finally:
            conn.close()

        return TopicData(
            topic_id=topic_id,
            agent_id=agent_id,
            title=title,
            description=description,
            source_url=source_url,
            source_name=source_name,
            discovered_at=now_utc,
            editorial_score=editorial_score,
            status=status
        )

    def get_topic(self, topic_id: str) -> Optional[TopicData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT topic_id, agent_id, title, description, source_url, source_name, discovered_at, editorial_score, status
                FROM topics WHERE topic_id = ?
                """,
                (topic_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return TopicData(
                topic_id=row["topic_id"],
                agent_id=row["agent_id"],
                title=row["title"],
                description=row["description"],
                source_url=row["source_url"],
                source_name=row["source_name"],
                discovered_at=row["discovered_at"],
                editorial_score=row["editorial_score"],
                status=row["status"]
            )
        finally:
            conn.close()

    def list_topics_by_agent(self, agent_id: str) -> List[TopicData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT topic_id, agent_id, title, description, source_url, source_name, discovered_at, editorial_score, status
                FROM topics WHERE agent_id = ? ORDER BY discovered_at DESC
                """,
                (agent_id,)
            )
            rows = cursor.fetchall()
            return [
                TopicData(
                    topic_id=row["topic_id"],
                    agent_id=row["agent_id"],
                    title=row["title"],
                    description=row["description"],
                    source_url=row["source_url"],
                    source_name=row["source_name"],
                    discovered_at=row["discovered_at"],
                    editorial_score=row["editorial_score"],
                    status=row["status"]
                )
                for row in rows
            ]
        finally:
            conn.close()


def get_topic_repository() -> BaseTopicRepository:
    """Dependency provider for TopicRepository."""
    return SQLiteTopicRepository()
