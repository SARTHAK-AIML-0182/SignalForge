import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Union

from app.db.database import get_connection


@dataclass
class PostData:
    post_id: str
    agent_id: str
    text: str
    topic_id: Optional[str] = None
    rationale: Optional[str] = None
    sources: List[Any] = field(default_factory=list)
    editorial_score: float = 0.0
    created_at: Optional[str] = None


class BasePostRepository(ABC):
    @abstractmethod
    def create_post(
        self,
        post_id: str,
        agent_id: str,
        text: str,
        topic_id: Optional[str] = None,
        rationale: Optional[str] = None,
        sources: Optional[List[Any]] = None,
        editorial_score: float = 0.0
    ) -> PostData:
        """Create a new post entity."""
        pass

    @abstractmethod
    def get_post(self, post_id: str) -> Optional[PostData]:
        """Retrieve post by ID."""
        pass

    @abstractmethod
    def list_posts_by_agent(self, agent_id: str) -> List[PostData]:
        """List all posts for an agent."""
        pass


class SQLitePostRepository(BasePostRepository):
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path

    def create_post(
        self,
        post_id: str,
        agent_id: str,
        text: str,
        topic_id: Optional[str] = None,
        rationale: Optional[str] = None,
        sources: Optional[List[Any]] = None,
        editorial_score: float = 0.0
    ) -> PostData:
        now_utc = datetime.now(timezone.utc).isoformat()
        sources_list = sources if sources is not None else []
        sources_json = json.dumps(sources_list)

        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO posts (
                        post_id, agent_id, topic_id, text, rationale, sources, editorial_score, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (post_id, agent_id, topic_id, text, rationale, sources_json, editorial_score, now_utc)
                )
        finally:
            conn.close()

        return PostData(
            post_id=post_id,
            agent_id=agent_id,
            topic_id=topic_id,
            text=text,
            rationale=rationale,
            sources=sources_list,
            editorial_score=editorial_score,
            created_at=now_utc
        )

    def get_post(self, post_id: str) -> Optional[PostData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT post_id, agent_id, topic_id, text, rationale, sources, editorial_score, created_at
                FROM posts WHERE post_id = ?
                """,
                (post_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            raw_sources = row["sources"]
            try:
                parsed_sources = json.loads(raw_sources) if raw_sources else []
            except json.JSONDecodeError:
                parsed_sources = []

            return PostData(
                post_id=row["post_id"],
                agent_id=row["agent_id"],
                topic_id=row["topic_id"],
                text=row["text"],
                rationale=row["rationale"],
                sources=parsed_sources,
                editorial_score=row["editorial_score"],
                created_at=row["created_at"]
            )
        finally:
            conn.close()

    def list_posts_by_agent(self, agent_id: str) -> List[PostData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT post_id, agent_id, topic_id, text, rationale, sources, editorial_score, created_at
                FROM posts WHERE agent_id = ? ORDER BY created_at DESC
                """,
                (agent_id,)
            )
            rows = cursor.fetchall()
            posts = []
            for row in rows:
                raw_sources = row["sources"]
                try:
                    parsed_sources = json.loads(raw_sources) if raw_sources else []
                except json.JSONDecodeError:
                    parsed_sources = []
                posts.append(
                    PostData(
                        post_id=row["post_id"],
                        agent_id=row["agent_id"],
                        topic_id=row["topic_id"],
                        text=row["text"],
                        rationale=row["rationale"],
                        sources=parsed_sources,
                        editorial_score=row["editorial_score"],
                        created_at=row["created_at"]
                    )
                )
            return posts
        finally:
            conn.close()


def get_post_repository() -> BasePostRepository:
    """Dependency provider for PostRepository."""
    return SQLitePostRepository()
