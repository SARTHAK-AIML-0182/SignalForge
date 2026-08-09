import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

from app.db.database import get_connection
from app.services.workflow.models import (
    AgentWorkflowResult,
    WorkflowStageResult,
)


class BaseWorkflowRepository(ABC):
    @abstractmethod
    def save_workflow(self, result: AgentWorkflowResult) -> AgentWorkflowResult:
        """Create or update complete workflow execution record and stage results."""
        pass

    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Optional[AgentWorkflowResult]:
        """Retrieve workflow execution by ID with ordered stages and traceability."""
        pass

    @abstractmethod
    def list_workflows_by_agent(
        self, agent_id: str, limit: int = 20, offset: int = 0
    ) -> List[AgentWorkflowResult]:
        """List historical workflows for an agent ordered by started_at DESC."""
        pass

    @abstractmethod
    def count_workflows_by_agent(self, agent_id: str) -> int:
        """Count total workflow runs for an agent."""
        pass


class SQLiteWorkflowRepository(BaseWorkflowRepository):
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path

    def save_workflow(self, result: AgentWorkflowResult) -> AgentWorkflowResult:
        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO workflows (
                        workflow_id, agent_id, status, started_at, completed_at,
                        is_successful, halted_at_stage, rationale, selected_topic_ids,
                        research_ids, draft_ids, publication_ids, traceability
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(workflow_id) DO UPDATE SET
                        status = excluded.status,
                        completed_at = excluded.completed_at,
                        is_successful = excluded.is_successful,
                        halted_at_stage = excluded.halted_at_stage,
                        rationale = excluded.rationale,
                        selected_topic_ids = excluded.selected_topic_ids,
                        research_ids = excluded.research_ids,
                        draft_ids = excluded.draft_ids,
                        publication_ids = excluded.publication_ids,
                        traceability = excluded.traceability
                    """,
                    (
                        result.workflow_id,
                        result.agent_id,
                        result.status,
                        result.started_at,
                        result.completed_at,
                        1 if result.is_successful else 0,
                        result.halted_at_stage,
                        result.rationale,
                        json.dumps(result.selected_topic_ids or []),
                        json.dumps(result.research_ids or []),
                        json.dumps(result.draft_ids or []),
                        json.dumps(result.publication_ids or []),
                        json.dumps(result.traceability or {}),
                    ),
                )

                conn.execute(
                    "DELETE FROM workflow_stages WHERE workflow_id = ?",
                    (result.workflow_id,),
                )

                for idx, stage in enumerate(result.stages):
                    conn.execute(
                        """
                        INSERT INTO workflow_stages (
                            workflow_id, stage_name, status, started_at, completed_at,
                            is_successful, rationale, entity_ids, metadata, stage_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            result.workflow_id,
                            stage.stage_name,
                            stage.status,
                            stage.started_at,
                            stage.completed_at,
                            1 if stage.is_successful else 0,
                            stage.rationale,
                            json.dumps(stage.entity_ids or {}),
                            json.dumps(stage.metadata or {}),
                            idx,
                        ),
                    )
        finally:
            conn.close()

        return result

    def get_workflow(self, workflow_id: str) -> Optional[AgentWorkflowResult]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT workflow_id, agent_id, status, started_at, completed_at,
                       is_successful, halted_at_stage, rationale, selected_topic_ids,
                       research_ids, draft_ids, publication_ids, traceability
                FROM workflows WHERE workflow_id = ?
                """,
                (workflow_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            stage_cursor = conn.execute(
                """
                SELECT stage_name, status, started_at, completed_at, is_successful,
                       rationale, entity_ids, metadata
                FROM workflow_stages
                WHERE workflow_id = ? ORDER BY stage_order ASC
                """,
                (workflow_id,),
            )
            stage_rows = stage_cursor.fetchall()

            stages = [
                WorkflowStageResult(
                    stage_name=st_row["stage_name"],
                    status=st_row["status"],
                    started_at=st_row["started_at"],
                    completed_at=st_row["completed_at"],
                    is_successful=bool(st_row["is_successful"]),
                    rationale=st_row["rationale"] or "",
                    entity_ids=json.loads(st_row["entity_ids"] or "{}"),
                    metadata=json.loads(st_row["metadata"] or "{}"),
                )
                for st_row in stage_rows
            ]

            return AgentWorkflowResult(
                workflow_id=row["workflow_id"],
                agent_id=row["agent_id"],
                status=row["status"],
                started_at=row["started_at"],
                completed_at=row["completed_at"] or "",
                stages=stages,
                selected_topic_ids=json.loads(row["selected_topic_ids"] or "[]"),
                research_ids=json.loads(row["research_ids"] or "[]"),
                draft_ids=json.loads(row["draft_ids"] or "[]"),
                publication_ids=json.loads(row["publication_ids"] or "[]"),
                is_successful=bool(row["is_successful"]),
                halted_at_stage=row["halted_at_stage"],
                rationale=row["rationale"] or "",
                traceability=json.loads(row["traceability"] or "{}"),
            )
        finally:
            conn.close()

    def list_workflows_by_agent(
        self, agent_id: str, limit: int = 20, offset: int = 0
    ) -> List[AgentWorkflowResult]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT workflow_id, agent_id, status, started_at, completed_at,
                       is_successful, halted_at_stage, rationale, selected_topic_ids,
                       research_ids, draft_ids, publication_ids, traceability
                FROM workflows WHERE agent_id = ?
                ORDER BY started_at DESC LIMIT ? OFFSET ?
                """,
                (agent_id, limit, offset),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                stage_cursor = conn.execute(
                    """
                    SELECT stage_name, status, started_at, completed_at, is_successful,
                           rationale, entity_ids, metadata
                    FROM workflow_stages
                    WHERE workflow_id = ? ORDER BY stage_order ASC
                    """,
                    (row["workflow_id"],),
                )
                stage_rows = stage_cursor.fetchall()
                stages = [
                    WorkflowStageResult(
                        stage_name=st_row["stage_name"],
                        status=st_row["status"],
                        started_at=st_row["started_at"],
                        completed_at=st_row["completed_at"],
                        is_successful=bool(st_row["is_successful"]),
                        rationale=st_row["rationale"] or "",
                        entity_ids=json.loads(st_row["entity_ids"] or "{}"),
                        metadata=json.loads(st_row["metadata"] or "{}"),
                    )
                    for st_row in stage_rows
                ]

                results.append(
                    AgentWorkflowResult(
                        workflow_id=row["workflow_id"],
                        agent_id=row["agent_id"],
                        status=row["status"],
                        started_at=row["started_at"],
                        completed_at=row["completed_at"] or "",
                        stages=stages,
                        selected_topic_ids=json.loads(row["selected_topic_ids"] or "[]"),
                        research_ids=json.loads(row["research_ids"] or "[]"),
                        draft_ids=json.loads(row["draft_ids"] or "[]"),
                        publication_ids=json.loads(row["publication_ids"] or "[]"),
                        is_successful=bool(row["is_successful"]),
                        halted_at_stage=row["halted_at_stage"],
                        rationale=row["rationale"] or "",
                        traceability=json.loads(row["traceability"] or "{}"),
                    )
                )
            return results
        finally:
            conn.close()

    def count_workflows_by_agent(self, agent_id: str) -> int:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) as cnt FROM workflows WHERE agent_id = ?",
                (agent_id,),
            )
            row = cursor.fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()


def get_workflow_repository() -> BaseWorkflowRepository:
    """Dependency provider for WorkflowRepository."""
    return SQLiteWorkflowRepository()
