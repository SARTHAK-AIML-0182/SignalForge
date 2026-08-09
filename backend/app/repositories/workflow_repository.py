import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.db.database import get_connection
from app.services.workflow.models import (
    AgentWorkflowResult,
    WorkflowStageResult,
)


def calculate_duration_seconds(started_at: str, completed_at: Optional[str]) -> Optional[float]:
    """Calculate workflow execution duration in seconds, or None if incomplete/invalid."""
    if not started_at or not completed_at:
        return None
    try:
        dt_start = datetime.fromisoformat(started_at)
        dt_end = datetime.fromisoformat(completed_at)
        diff = (dt_end - dt_start).total_seconds()
        return max(0.0, round(diff, 3))
    except (ValueError, TypeError):
        return None


def calculate_stage_stats(stages: List[WorkflowStageResult]) -> dict:
    """Calculate deterministic stage counts by status."""
    total = len(stages)
    succeeded = sum(1 for s in stages if s.status == "SUCCEEDED")
    failed = sum(1 for s in stages if s.status == "FAILED")
    blocked = sum(1 for s in stages if s.status == "BLOCKED")
    skipped = sum(1 for s in stages if s.status == "SKIPPED")
    running = sum(1 for s in stages if s.status == "RUNNING")
    return {
        "total_stages": total,
        "succeeded_stages": succeeded,
        "failed_stages": failed,
        "blocked_stages": blocked,
        "skipped_stages": skipped,
        "running_stages": running,
    }


def extract_traceability_summary(traceability: dict) -> dict:
    """Extract concise traceability summary mapping from raw traceability dictionary."""
    summary = {}
    if not isinstance(traceability, dict):
        return summary

    for topic_id, item in traceability.items():
        if isinstance(item, dict):
            summary[topic_id] = {
                "topic_id": item.get("topic_id", topic_id),
                "title": item.get("title", ""),
                "research_id": item.get("research_id"),
                "draft_id": item.get("draft_id"),
                "publication_id": item.get("publication_id"),
                "is_publishable": item.get("is_publishable", False),
                "finding_count": len(item.get("finding_ids") or []),
                "claim_count": len(item.get("claim_ids") or []),
            }
    return summary


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
        self,
        agent_id: str,
        status: Optional[str] = None,
        is_successful: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[AgentWorkflowResult]:
        """List historical workflows for an agent ordered by started_at DESC with optional filtering."""
        pass

    @abstractmethod
    def count_workflows_by_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
        is_successful: Optional[bool] = None,
    ) -> int:
        """Count total workflow runs for an agent matching optional filters."""
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
                        research_ids, draft_ids, publication_ids, traceability, policy, governance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        traceability = excluded.traceability,
                        policy = excluded.policy,
                        governance = excluded.governance
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
                        json.dumps(result.policy or {}),
                        json.dumps(result.governance or {}),
                    ),
                )

                conn.execute(
                    "DELETE FROM workflow_stages WHERE workflow_id = ?",
                    (result.workflow_id,),
                )

                if result.stages:
                    stage_tuples = [
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
                        )
                        for idx, stage in enumerate(result.stages)
                    ]
                    conn.executemany(
                        """
                        INSERT INTO workflow_stages (
                            workflow_id, stage_name, status, started_at, completed_at,
                            is_successful, rationale, entity_ids, metadata, stage_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        stage_tuples,
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
                       research_ids, draft_ids, publication_ids, traceability, policy, governance
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

            raw_policy = row["policy"] if "policy" in row.keys() else "{}"
            parsed_policy = json.loads(raw_policy) if raw_policy and raw_policy != "{}" else None

            raw_gov = row["governance"] if "governance" in row.keys() else "{}"
            parsed_gov = json.loads(raw_gov) if raw_gov and raw_gov != "{}" else None

            parsed_traceability = json.loads(row["traceability"] or "{}")
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
                traceability=parsed_traceability,
                policy=parsed_policy,
                governance=parsed_gov,
                diagnostics=parsed_traceability.get("diagnostics", []),
            )
        finally:
            conn.close()

    def list_workflows_by_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
        is_successful: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[AgentWorkflowResult]:
        conn = get_connection(self.db_path)
        try:
            query = """
                SELECT workflow_id, agent_id, status, started_at, completed_at,
                       is_successful, halted_at_stage, rationale, selected_topic_ids,
                       research_ids, draft_ids, publication_ids, traceability, policy, governance
                FROM workflows WHERE agent_id = ?
            """
            params: List[Union[str, int]] = [agent_id]

            if status is not None:
                query += " AND status = ?"
                params.append(status)

            if is_successful is not None:
                query += " AND is_successful = ?"
                params.append(1 if is_successful else 0)

            query += " ORDER BY started_at DESC, workflow_id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, tuple(params))
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

                raw_policy = row["policy"] if "policy" in row.keys() else "{}"
                parsed_policy = json.loads(raw_policy) if raw_policy and raw_policy != "{}" else None

                raw_gov = row["governance"] if "governance" in row.keys() else "{}"
                parsed_gov = json.loads(raw_gov) if raw_gov and raw_gov != "{}" else None

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
                        policy=parsed_policy,
                        governance=parsed_gov,
                    )
                )
            return results
        finally:
            conn.close()

    def count_workflows_by_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
        is_successful: Optional[bool] = None,
    ) -> int:
        conn = get_connection(self.db_path)
        try:
            query = "SELECT COUNT(*) as cnt FROM workflows WHERE agent_id = ?"
            params: List[Union[str, int]] = [agent_id]

            if status is not None:
                query += " AND status = ?"
                params.append(status)

            if is_successful is not None:
                query += " AND is_successful = ?"
                params.append(1 if is_successful else 0)

            cursor = conn.execute(query, tuple(params))
            row = cursor.fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()


def get_workflow_repository() -> BaseWorkflowRepository:
    """Dependency provider for WorkflowRepository."""
    return SQLiteWorkflowRepository()
