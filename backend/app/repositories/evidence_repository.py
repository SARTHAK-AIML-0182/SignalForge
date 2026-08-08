from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from app.db.database import get_connection


@dataclass
class EvidenceData:
    evidence_id: str
    research_id: str
    source_url: str
    source_name: str
    title: str
    content: str
    source_type: str = "web"
    retrieved_at: Optional[str] = None
    confidence: float = 0.0


class BaseEvidenceRepository(ABC):
    @abstractmethod
    def create_evidence(
        self,
        evidence_id: str,
        research_id: str,
        source_url: str,
        source_name: str,
        title: str,
        content: str,
        source_type: str = "web",
        confidence: float = 0.0,
    ) -> EvidenceData:
        """Create a new evidence record."""
        pass

    @abstractmethod
    def get_evidence(self, evidence_id: str) -> Optional[EvidenceData]:
        """Retrieve evidence record by ID."""
        pass

    @abstractmethod
    def get_evidence_by_url(self, research_id: str, source_url: str) -> Optional[EvidenceData]:
        """Retrieve evidence record by research ID and source URL for duplicate checking."""
        pass

    @abstractmethod
    def list_evidence_by_research(self, research_id: str) -> List[EvidenceData]:
        """List all evidence records for a research investigation."""
        pass


class SQLiteEvidenceRepository(BaseEvidenceRepository):
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path

    def create_evidence(
        self,
        evidence_id: str,
        research_id: str,
        source_url: str,
        source_name: str,
        title: str,
        content: str,
        source_type: str = "web",
        confidence: float = 0.0,
    ) -> EvidenceData:
        now_utc = datetime.now(timezone.utc).isoformat()
        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO evidence (
                        evidence_id, research_id, source_url, source_name, source_type, title, retrieved_at, content, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (evidence_id, research_id, source_url, source_name, source_type, title, now_utc, content, confidence),
                )
        finally:
            conn.close()

        return EvidenceData(
            evidence_id=evidence_id,
            research_id=research_id,
            source_url=source_url,
            source_name=source_name,
            title=title,
            content=content,
            source_type=source_type,
            retrieved_at=now_utc,
            confidence=confidence,
        )

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT evidence_id, research_id, source_url, source_name, source_type, title, retrieved_at, content, confidence
                FROM evidence WHERE evidence_id = ?
                """,
                (evidence_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return EvidenceData(
                evidence_id=row["evidence_id"],
                research_id=row["research_id"],
                source_url=row["source_url"],
                source_name=row["source_name"],
                source_type=row["source_type"],
                title=row["title"],
                retrieved_at=row["retrieved_at"],
                content=row["content"],
                confidence=row["confidence"],
            )
        finally:
            conn.close()

    def get_evidence_by_url(self, research_id: str, source_url: str) -> Optional[EvidenceData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT evidence_id, research_id, source_url, source_name, source_type, title, retrieved_at, content, confidence
                FROM evidence WHERE research_id = ? AND LOWER(TRIM(source_url)) = LOWER(TRIM(?))
                """,
                (research_id, source_url),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return EvidenceData(
                evidence_id=row["evidence_id"],
                research_id=row["research_id"],
                source_url=row["source_url"],
                source_name=row["source_name"],
                source_type=row["source_type"],
                title=row["title"],
                retrieved_at=row["retrieved_at"],
                content=row["content"],
                confidence=row["confidence"],
            )
        finally:
            conn.close()

    def list_evidence_by_research(self, research_id: str) -> List[EvidenceData]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT evidence_id, research_id, source_url, source_name, source_type, title, retrieved_at, content, confidence
                FROM evidence WHERE research_id = ? ORDER BY retrieved_at ASC
                """,
                (research_id,),
            )
            rows = cursor.fetchall()
            return [
                EvidenceData(
                    evidence_id=row["evidence_id"],
                    research_id=row["research_id"],
                    source_url=row["source_url"],
                    source_name=row["source_name"],
                    source_type=row["source_type"],
                    title=row["title"],
                    retrieved_at=row["retrieved_at"],
                    content=row["content"],
                    confidence=row["confidence"],
                )
                for row in rows
            ]
        finally:
            conn.close()


def get_evidence_repository() -> BaseEvidenceRepository:
    """Dependency provider for EvidenceRepository."""
    return SQLiteEvidenceRepository()
