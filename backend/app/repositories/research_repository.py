import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from app.db.database import get_connection


@dataclass
class ResearchData:
    research_id: str
    agent_id: str
    topic_id: str
    status: str = "pending"
    confidence: float = 0.0
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class BaseResearchRepository(ABC):
    @abstractmethod
    def create_research(
        self,
        research_id: str,
        agent_id: str,
        topic_id: str,
        status: str = "pending",
        confidence: float = 0.0,
    ) -> ResearchData:
        """Create a new research investigation."""
        pass

    @abstractmethod
    def get_research(self, research_id: str) -> Optional[ResearchData]:
        """Retrieve research investigation by ID."""
        pass

    @abstractmethod
    def get_research_by_topic(self, topic_id: str) -> Optional[ResearchData]:
        """Retrieve research investigation for a specific topic."""
        pass

    @abstractmethod
    def update_research_status(self, research_id: str, status: str) -> Optional[ResearchData]:
        """Update status of a research investigation."""
        pass

    @abstractmethod
    def update_research_confidence(self, research_id: str, confidence: float) -> Optional[ResearchData]:
        """Update confidence score of a research investigation."""
        pass

    @abstractmethod
    def complete_research(
        self,
        research_id: str,
        confidence: Optional[float] = None,
        status: str = "completed",
    ) -> Optional[ResearchData]:
        """Mark research investigation as completed and record completion timestamp."""
        pass


class SQLiteResearchRepository(BaseResearchRepository):
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path

    def create_research(
        self,
        research_id: str,
        agent_id: str,
        topic_id: str,
        status: str = "pending",
        confidence: float = 0.0,
    ) -> ResearchData:
        existing = self.get_research_by_topic(topic_id)
        if existing:
            raise ValueError(f"Research investigation already exists for topic_id '{topic_id}'")

        now_utc = datetime.now(timezone.utc).isoformat()
        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO research (
                        research_id, agent_id, topic_id, status, confidence, created_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (research_id, agent_id, topic_id, status, confidence, now_utc, None),
                )
        finally:
            conn.close()

        return ResearchData(
            research_id=research_id,
            agent_id=agent_id,
            topic_id=topic_id,
            status=status,
            confidence=confidence,
            created_at=now_utc,
            completed_at=None,
        )

    def get_research(self, research_id: str) -> Optional[ResearchData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT research_id, agent_id, topic_id, status, confidence, created_at, completed_at
                FROM research WHERE research_id = ?
                """,
                (research_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return ResearchData(
                research_id=row["research_id"],
                agent_id=row["agent_id"],
                topic_id=row["topic_id"],
                status=row["status"],
                confidence=row["confidence"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )
        finally:
            conn.close()

    def get_research_by_topic(self, topic_id: str) -> Optional[ResearchData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT research_id, agent_id, topic_id, status, confidence, created_at, completed_at
                FROM research WHERE topic_id = ?
                """,
                (topic_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return ResearchData(
                research_id=row["research_id"],
                agent_id=row["agent_id"],
                topic_id=row["topic_id"],
                status=row["status"],
                confidence=row["confidence"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )
        finally:
            conn.close()

    def update_research_status(self, research_id: str, status: str) -> Optional[ResearchData]:
        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    "UPDATE research SET status = ? WHERE research_id = ?",
                    (status, research_id),
                )
        finally:
            conn.close()

        return self.get_research(research_id)

    def update_research_confidence(self, research_id: str, confidence: float) -> Optional[ResearchData]:
        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    "UPDATE research SET confidence = ? WHERE research_id = ?",
                    (confidence, research_id),
                )
        finally:
            conn.close()

        return self.get_research(research_id)

    def complete_research(
        self,
        research_id: str,
        confidence: Optional[float] = None,
        status: str = "completed",
    ) -> Optional[ResearchData]:
        now_utc = datetime.now(timezone.utc).isoformat()
        conn = get_connection(self.db_path)
        try:
            with conn:
                if confidence is not None:
                    conn.execute(
                        "UPDATE research SET status = ?, confidence = ?, completed_at = ? WHERE research_id = ?",
                        (status, confidence, now_utc, research_id),
                    )
                else:
                    conn.execute(
                        "UPDATE research SET status = ?, completed_at = ? WHERE research_id = ?",
                        (status, now_utc, research_id),
                    )
        finally:
            conn.close()

        return self.get_research(research_id)


def get_research_repository() -> BaseResearchRepository:
    """Dependency provider for ResearchRepository."""
    return SQLiteResearchRepository()
