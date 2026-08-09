import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.repositories.agent_repository import (
    BaseAgentRepository,
    SQLiteAgentRepository,
    get_agent_repository,
)
from app.repositories.evidence_repository import (
    BaseEvidenceRepository,
    SQLiteEvidenceRepository,
    get_evidence_repository,
)
from app.repositories.research_repository import (
    BaseResearchRepository,
    SQLiteResearchRepository,
    get_research_repository,
)
from app.repositories.topic_repository import (
    BaseTopicRepository,
    SQLiteTopicRepository,
    get_topic_repository,
)
from app.services.discovery import discover_topics
from app.services.editorial import evaluate_agent_topics
from app.services.publishing import BasePublishingAdapter, publish_draft
from app.services.research import (
    build_content_brief,
    generate_draft,
    research_topic,
    synthesize_research,
    validate_research,
)
from app.services.workflow.models import (
    AgentWorkflowResult,
    WorkflowConfig,
    WorkflowStageResult,
    WorkflowStageStatus,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


def run_agent_workflow(
    agent_id: str,
    config: Optional[WorkflowConfig] = None,
    agent_repo: Optional[BaseAgentRepository] = None,
    topic_repo: Optional[BaseTopicRepository] = None,
    research_repo: Optional[BaseResearchRepository] = None,
    evidence_repo: Optional[BaseEvidenceRepository] = None,
    workflow_repo: Optional[Any] = None,
    http_client: Optional[httpx.Client] = None,
    publishing_adapter: Optional[BasePublishingAdapter] = None,
    feeds: Optional[List[Any]] = None,
) -> AgentWorkflowResult:
    """
    Execute the complete 9-stage SignalForge autonomous AI persona workflow deterministically.
    Stages: Discovery -> Editorial -> Research -> Validation -> Synthesis -> Brief -> Writer -> Gate -> Dry-Run Publishing.
    Isolates topic-level failures and maintains full 9-stage end-to-end traceability.
    """
    started_at = datetime.now(timezone.utc).isoformat()
    workflow_id = f"wf-{secrets.token_hex(8)}"

    if config is None:
        config = WorkflowConfig()

    db_path = None
    for r in [topic_repo, agent_repo, research_repo, evidence_repo, workflow_repo]:
        if r is not None and hasattr(r, "db_path"):
            db_path = r.db_path
            break

    if agent_repo is None:
        agent_repo = SQLiteAgentRepository(db_path) if db_path else get_agent_repository()
    if topic_repo is None:
        topic_repo = SQLiteTopicRepository(db_path) if db_path else get_topic_repository()
    if research_repo is None:
        research_repo = SQLiteResearchRepository(db_path) if db_path else get_research_repository()
    if evidence_repo is None:
        evidence_repo = SQLiteEvidenceRepository(db_path) if db_path else get_evidence_repository()
    if workflow_repo is None:
        from app.repositories.workflow_repository import (
            SQLiteWorkflowRepository,
            get_workflow_repository,
        )
        workflow_repo = SQLiteWorkflowRepository(db_path) if db_path else get_workflow_repository()

    def _persist_result(res: AgentWorkflowResult) -> AgentWorkflowResult:
        try:
            workflow_repo.save_workflow(res)
            return res
        except Exception as save_err:
            logger.error(f"Failed to persist workflow {res.workflow_id}: {save_err}")
            if res.status != WorkflowStatus.FAILED:
                return AgentWorkflowResult(
                    workflow_id=res.workflow_id,
                    agent_id=res.agent_id,
                    status=WorkflowStatus.FAILED,
                    started_at=res.started_at,
                    completed_at=res.completed_at or datetime.now(timezone.utc).isoformat(),
                    stages=res.stages,
                    selected_topic_ids=res.selected_topic_ids,
                    research_ids=res.research_ids,
                    draft_ids=res.draft_ids,
                    publication_ids=res.publication_ids,
                    is_successful=False,
                    halted_at_stage="persistence",
                    rationale="Workflow execution completed, but persisting final workflow state failed.",
                    traceability=res.traceability,
                )
            return res

    stages: List[WorkflowStageResult] = []
    selected_topic_ids: List[str] = []
    research_ids: List[str] = []
    draft_ids: List[str] = []
    publication_ids: List[str] = []
    traceability: Dict[str, Any] = {}

    # Persist initial RUNNING status record
    _persist_result(
        AgentWorkflowResult(
            workflow_id=workflow_id,
            agent_id=agent_id,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            completed_at="",
            stages=[],
            selected_topic_ids=[],
            research_ids=[],
            draft_ids=[],
            publication_ids=[],
            is_successful=False,
            halted_at_stage=None,
            rationale="Workflow execution in progress.",
            traceability={},
        )
    )

    try:
        # ------------------------------------------------------------------
        # STAGE 1 — TOPIC DISCOVERY
        # ------------------------------------------------------------------
        s1_start = datetime.now(timezone.utc).isoformat()
        try:
            discovered_topics = discover_topics(
                agent_id=agent_id,
                repo=topic_repo,
                feeds=feeds,
                http_client=http_client,
            )
            s1_end = datetime.now(timezone.utc).isoformat()

            disc_topic_ids = [t.topic_id for t in discovered_topics]
            stages.append(
                WorkflowStageResult(
                    stage_name="topic_discovery",
                    status=WorkflowStageStatus.SUCCEEDED,
                    started_at=s1_start,
                    completed_at=s1_end,
                    is_successful=True,
                    rationale=f"Successfully discovered {len(discovered_topics)} topics.",
                    entity_ids={"topic_ids": disc_topic_ids},
                    metadata={"discovered_count": len(discovered_topics)},
                )
            )
        except Exception as exc:
            s1_end = datetime.now(timezone.utc).isoformat()
            logger.error(f"Topic discovery failed completely: {exc}")
            stages.append(
                WorkflowStageResult(
                    stage_name="topic_discovery",
                    status=WorkflowStageStatus.FAILED,
                    started_at=s1_start,
                    completed_at=s1_end,
                    is_successful=False,
                    rationale=f"Topic discovery failed with exception: {type(exc).__name__}",
                    entity_ids={},
                )
            )
            completed_at = datetime.now(timezone.utc).isoformat()
            return _persist_result(
                AgentWorkflowResult(
                    workflow_id=workflow_id,
                    agent_id=agent_id,
                    status=WorkflowStatus.FAILED,
                    started_at=started_at,
                    completed_at=completed_at,
                    stages=stages,
                    selected_topic_ids=[],
                    research_ids=[],
                    draft_ids=[],
                    publication_ids=[],
                    is_successful=False,
                    halted_at_stage="topic_discovery",
                    rationale="Workflow halted: Topic discovery failed completely.",
                    traceability={},
                )
            )

        # ------------------------------------------------------------------
        # STAGE 2 — EDITORIAL EVALUATION
        # ------------------------------------------------------------------
        s2_start = datetime.now(timezone.utc).isoformat()
        try:
            editorial_decisions = evaluate_agent_topics(
                agent_id=agent_id,
                repo=topic_repo,
                threshold=config.editorial_threshold,
            )
            s2_end = datetime.now(timezone.utc).isoformat()

            selected_decisions = [d for d in editorial_decisions if d.decision == "selected"]
            selected_topic_ids = [d.topic_id for d in selected_decisions]

            stages.append(
                WorkflowStageResult(
                    stage_name="editorial_evaluation",
                    status=WorkflowStageStatus.SUCCEEDED,
                    started_at=s2_start,
                    completed_at=s2_end,
                    is_successful=True,
                    rationale=f"Evaluated {len(editorial_decisions)} topics. Selected {len(selected_decisions)} topics.",
                    entity_ids={"selected_topic_ids": selected_topic_ids},
                    metadata={
                        "total_evaluated": len(editorial_decisions),
                        "selected_count": len(selected_decisions),
                    },
                )
            )
        except Exception as exc:
            s2_end = datetime.now(timezone.utc).isoformat()
            logger.error(f"Editorial evaluation failed: {exc}")
            stages.append(
                WorkflowStageResult(
                    stage_name="editorial_evaluation",
                    status=WorkflowStageStatus.FAILED,
                    started_at=s2_start,
                    completed_at=s2_end,
                    is_successful=False,
                    rationale=f"Editorial evaluation failed with exception: {type(exc).__name__}",
                    entity_ids={},
                )
            )
            completed_at = datetime.now(timezone.utc).isoformat()
            return _persist_result(
                AgentWorkflowResult(
                    workflow_id=workflow_id,
                    agent_id=agent_id,
                    status=WorkflowStatus.FAILED,
                    started_at=started_at,
                    completed_at=completed_at,
                    stages=stages,
                    selected_topic_ids=[],
                    research_ids=[],
                    draft_ids=[],
                    publication_ids=[],
                    is_successful=False,
                    halted_at_stage="editorial_evaluation",
                    rationale="Workflow halted: Editorial evaluation failed.",
                    traceability={},
                )
            )

        # Early exit if zero topics passed editorial selection
        if not selected_topic_ids:
            s_now = datetime.now(timezone.utc).isoformat()
            for st_name in [
                "research",
                "research_validation",
                "research_synthesis",
                "content_brief",
                "draft_generation",
                "publishability_check",
                "dry_run_publication",
            ]:
                stages.append(
                    WorkflowStageResult(
                        stage_name=st_name,
                        status=WorkflowStageStatus.SKIPPED,
                        started_at=s_now,
                        completed_at=s_now,
                        is_successful=True,
                        rationale="Skipped because no topic passed editorial selection.",
                        entity_ids={},
                    )
                )

            completed_at = datetime.now(timezone.utc).isoformat()
            return _persist_result(
                AgentWorkflowResult(
                    workflow_id=workflow_id,
                    agent_id=agent_id,
                    status=WorkflowStatus.NO_CONTENT,
                    started_at=started_at,
                    completed_at=completed_at,
                    stages=stages,
                    selected_topic_ids=[],
                    research_ids=[],
                    draft_ids=[],
                    publication_ids=[],
                    is_successful=True,
                    halted_at_stage=None,
                    rationale="NO CONTENT: Workflow completed cleanly, but zero topics met the editorial selection threshold.",
                    traceability={},
                )
            )

        # ------------------------------------------------------------------
        # STAGES 3 TO 9 — PER-TOPIC PIPELINE (WITH FAILURE ISOLATION)
        # ------------------------------------------------------------------
        topics_to_process = selected_topic_ids[: config.max_topics]
        successful_publications = 0
        blocked_publications = 0

        for topic_id in topics_to_process:
            topic_data = topic_repo.get_topic(topic_id)
            if not topic_data:
                continue

            topic_trace: Dict[str, Any] = {"topic_id": topic_id, "title": topic_data.title}
            traceability[topic_id] = topic_trace

            # STAGE 3 — Research
            s3_start = datetime.now(timezone.utc).isoformat()
            try:
                res_result = research_topic(
                    topic=topic_data,
                    research_repo=research_repo,
                    evidence_repo=evidence_repo,
                    http_client=http_client,
                    max_sources=config.max_research_items,
                )
                s3_end = datetime.now(timezone.utc).isoformat()

                if res_result.status == "failed" or res_result.evidence_count == 0:
                    stages.append(
                        WorkflowStageResult(
                            stage_name=f"research_{topic_id}",
                            status=WorkflowStageStatus.FAILED,
                            started_at=s3_start,
                            completed_at=s3_end,
                            is_successful=False,
                            rationale=f"Research failed or collected zero evidence for topic '{topic_id}'.",
                            entity_ids={"topic_ids": [topic_id]},
                        )
                    )
                    topic_trace["research_status"] = "failed"
                    continue

                research_ids.append(res_result.research_id)
                topic_trace["research_id"] = res_result.research_id
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"research_{topic_id}",
                        status=WorkflowStageStatus.SUCCEEDED,
                        started_at=s3_start,
                        completed_at=s3_end,
                        is_successful=True,
                        rationale=f"Gathered {res_result.evidence_count} evidence items (confidence: {res_result.confidence:.2f}).",
                        entity_ids={"topic_ids": [topic_id], "research_ids": [res_result.research_id]},
                    )
                )
            except Exception as exc:
                s3_end = datetime.now(timezone.utc).isoformat()
                logger.error(f"Research failed for topic {topic_id}: {exc}")
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"research_{topic_id}",
                        status=WorkflowStageStatus.FAILED,
                        started_at=s3_start,
                        completed_at=s3_end,
                        is_successful=False,
                        rationale=f"Research raised exception: {type(exc).__name__}",
                        entity_ids={"topic_ids": [topic_id]},
                    )
                )
                topic_trace["research_status"] = "exception"
                continue

            # STAGE 4 — Research Validation
            s4_start = datetime.now(timezone.utc).isoformat()
            try:
                val_result = validate_research(
                    research_id=res_result.research_id,
                    research_repo=research_repo,
                    evidence_repo=evidence_repo,
                    topic_repo=topic_repo,
                    threshold=config.validation_threshold,
                )
                s4_end = datetime.now(timezone.utc).isoformat()

                topic_trace["validation_classification"] = val_result.quality_classification
                topic_trace["validation_score"] = val_result.overall_score

                if not val_result.is_usable:
                    stages.append(
                        WorkflowStageResult(
                            stage_name=f"research_validation_{topic_id}",
                            status=WorkflowStageStatus.BLOCKED,
                            started_at=s4_start,
                            completed_at=s4_end,
                            is_successful=False,
                            rationale=f"Validation failed (classification: {val_result.quality_classification}, score: {val_result.overall_score:.2f}). Downstream pipeline blocked.",
                            entity_ids={"research_ids": [res_result.research_id]},
                        )
                    )
                    continue

                stages.append(
                    WorkflowStageResult(
                        stage_name=f"research_validation_{topic_id}",
                        status=WorkflowStageStatus.SUCCEEDED,
                        started_at=s4_start,
                        completed_at=s4_end,
                        is_successful=True,
                        rationale=val_result.rationale,
                        entity_ids={"research_ids": [res_result.research_id]},
                    )
                )
            except Exception as exc:
                s4_end = datetime.now(timezone.utc).isoformat()
                logger.error(f"Validation failed for research {res_result.research_id}: {exc}")
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"research_validation_{topic_id}",
                        status=WorkflowStageStatus.FAILED,
                        started_at=s4_start,
                        completed_at=s4_end,
                        is_successful=False,
                        rationale=f"Validation raised exception: {type(exc).__name__}",
                        entity_ids={"research_ids": [res_result.research_id]},
                    )
                )
                continue

            # STAGE 5 — Research Synthesis
            s5_start = datetime.now(timezone.utc).isoformat()
            try:
                synth_result = synthesize_research(
                    research_id=res_result.research_id,
                    research_repo=research_repo,
                    evidence_repo=evidence_repo,
                    topic_repo=topic_repo,
                    validation_threshold=config.validation_threshold,
                )
                s5_end = datetime.now(timezone.utc).isoformat()

                finding_ids = [f.finding_id for f in synth_result.findings]
                topic_trace["finding_ids"] = finding_ids

                stages.append(
                    WorkflowStageResult(
                        stage_name=f"research_synthesis_{topic_id}",
                        status=WorkflowStageStatus.SUCCEEDED,
                        started_at=s5_start,
                        completed_at=s5_end,
                        is_successful=True,
                        rationale=f"Synthesized {len(synth_result.findings)} findings across {synth_result.source_diversity_count} domain(s).",
                        entity_ids={"finding_ids": finding_ids},
                    )
                )
            except Exception as exc:
                s5_end = datetime.now(timezone.utc).isoformat()
                logger.error(f"Synthesis failed for research {res_result.research_id}: {exc}")
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"research_synthesis_{topic_id}",
                        status=WorkflowStageStatus.FAILED,
                        started_at=s5_start,
                        completed_at=s5_end,
                        is_successful=False,
                        rationale=f"Synthesis raised exception: {type(exc).__name__}",
                        entity_ids={"research_ids": [res_result.research_id]},
                    )
                )
                continue

            # STAGE 6 — Content Brief
            s6_start = datetime.now(timezone.utc).isoformat()
            try:
                brief_result = build_content_brief(
                    research_id=res_result.research_id,
                    research_repo=research_repo,
                    evidence_repo=evidence_repo,
                    topic_repo=topic_repo,
                    agent_repo=agent_repo,
                    validation_threshold=config.validation_threshold,
                )
                s6_end = datetime.now(timezone.utc).isoformat()

                claim_ids = [c.claim_id for c in brief_result.claims]
                topic_trace["claim_ids"] = claim_ids

                stages.append(
                    WorkflowStageResult(
                        stage_name=f"content_brief_{topic_id}",
                        status=WorkflowStageStatus.SUCCEEDED,
                        started_at=s6_start,
                        completed_at=s6_end,
                        is_successful=True,
                        rationale=f"Built content brief with {len(brief_result.claims)} supported claims and 6 writing constraints.",
                        entity_ids={"claim_ids": claim_ids},
                    )
                )
            except Exception as exc:
                s6_end = datetime.now(timezone.utc).isoformat()
                logger.error(f"Brief generation failed for research {res_result.research_id}: {exc}")
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"content_brief_{topic_id}",
                        status=WorkflowStageStatus.FAILED,
                        started_at=s6_start,
                        completed_at=s6_end,
                        is_successful=False,
                        rationale=f"Brief generation raised exception: {type(exc).__name__}",
                        entity_ids={"research_ids": [res_result.research_id]},
                    )
                )
                continue

            # STAGE 7 — Draft Generation
            s7_start = datetime.now(timezone.utc).isoformat()
            try:
                draft = generate_draft(brief_result)
                s7_end = datetime.now(timezone.utc).isoformat()

                draft_ids.append(draft.draft_id)
                topic_trace["draft_id"] = draft.draft_id
                topic_trace["is_publishable"] = draft.is_publishable

                stages.append(
                    WorkflowStageResult(
                        stage_name=f"draft_generation_{topic_id}",
                        status=WorkflowStageStatus.SUCCEEDED,
                        started_at=s7_start,
                        completed_at=s7_end,
                        is_successful=True,
                        rationale=f"Generated draft '{draft.draft_id}' with {len(draft.sections)} sections (is_publishable={draft.is_publishable}).",
                        entity_ids={"draft_ids": [draft.draft_id]},
                    )
                )
            except Exception as exc:
                s7_end = datetime.now(timezone.utc).isoformat()
                logger.error(f"Draft generation failed for brief on research {res_result.research_id}: {exc}")
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"draft_generation_{topic_id}",
                        status=WorkflowStageStatus.FAILED,
                        started_at=s7_start,
                        completed_at=s7_end,
                        is_successful=False,
                        rationale=f"Draft generation raised exception: {type(exc).__name__}",
                        entity_ids={"research_ids": [res_result.research_id]},
                    )
                )
                continue

            # STAGE 8 — Publishability Check
            s8_start = datetime.now(timezone.utc).isoformat()
            s8_end = datetime.now(timezone.utc).isoformat()
            if not draft.is_publishable:
                blocked_publications += 1
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"publishability_check_{topic_id}",
                        status=WorkflowStageStatus.BLOCKED,
                        started_at=s8_start,
                        completed_at=s8_end,
                        is_successful=False,
                        rationale=f"Draft '{draft.draft_id}' is marked unpublishable (warnings: {', '.join(draft.warnings)}).",
                        entity_ids={"draft_ids": [draft.draft_id]},
                    )
                )
                continue

            stages.append(
                WorkflowStageResult(
                    stage_name=f"publishability_check_{topic_id}",
                    status=WorkflowStageStatus.SUCCEEDED,
                    started_at=s8_start,
                    completed_at=s8_end,
                    is_successful=True,
                    rationale=f"Draft '{draft.draft_id}' passed publishability gate.",
                    entity_ids={"draft_ids": [draft.draft_id]},
                )
            )

            # STAGE 9 — Dry-Run Publication
            s9_start = datetime.now(timezone.utc).isoformat()
            if not config.enable_dry_run_publication:
                s9_end = datetime.now(timezone.utc).isoformat()
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"dry_run_publication_{topic_id}",
                        status=WorkflowStageStatus.SKIPPED,
                        started_at=s9_start,
                        completed_at=s9_end,
                        is_successful=True,
                        rationale="Dry-run publication is disabled in workflow configuration.",
                        entity_ids={"draft_ids": [draft.draft_id]},
                    )
                )
                continue

            try:
                pub_result = publish_draft(draft, adapter=publishing_adapter, dry_run=True)
                s9_end = datetime.now(timezone.utc).isoformat()

                publication_ids.append(pub_result.publication_id)
                topic_trace["publication_id"] = pub_result.publication_id
                topic_trace["publication_status"] = pub_result.status

                if pub_result.is_successful:
                    successful_publications += 1
                    stages.append(
                        WorkflowStageResult(
                            stage_name=f"dry_run_publication_{topic_id}",
                            status=WorkflowStageStatus.SUCCEEDED,
                            started_at=s9_start,
                            completed_at=s9_end,
                            is_successful=True,
                            rationale=pub_result.rationale,
                            entity_ids={
                                "draft_ids": [draft.draft_id],
                                "publication_ids": [pub_result.publication_id],
                            },
                        )
                    )
                else:
                    stages.append(
                        WorkflowStageResult(
                            stage_name=f"dry_run_publication_{topic_id}",
                            status=WorkflowStageStatus.BLOCKED,
                            started_at=s9_start,
                            completed_at=s9_end,
                            is_successful=False,
                            rationale=pub_result.rationale,
                            entity_ids={"draft_ids": [draft.draft_id]},
                        )
                    )
            except Exception as exc:
                s9_end = datetime.now(timezone.utc).isoformat()
                logger.error(f"Publication simulation failed for draft {draft.draft_id}: {exc}")
                stages.append(
                    WorkflowStageResult(
                        stage_name=f"dry_run_publication_{topic_id}",
                        status=WorkflowStageStatus.FAILED,
                        started_at=s9_start,
                        completed_at=s9_end,
                        is_successful=False,
                        rationale=f"Publication simulation raised exception: {type(exc).__name__}",
                        entity_ids={"draft_ids": [draft.draft_id]},
                    )
                )

        # Determine overall workflow status
        total_selected = len(topics_to_process)
        has_failed_stages = any(st.status == WorkflowStageStatus.FAILED for st in stages)
        first_failed_stage = next((st.stage_name for st in stages if st.status == WorkflowStageStatus.FAILED), None)

        if successful_publications == total_selected and total_selected > 0 and not has_failed_stages:
            overall_status = WorkflowStatus.SUCCESS
            workflow_rationale = (
                f"WORKFLOW SUCCESS: All {total_selected} selected topic(s) successfully executed "
                f"through all 9 stages and completed dry-run publication."
            )
        elif successful_publications > 0:
            overall_status = WorkflowStatus.PARTIAL_SUCCESS
            workflow_rationale = (
                f"WORKFLOW PARTIAL SUCCESS: {successful_publications} of {total_selected} selected topic(s) "
                f"successfully reached dry-run publication."
            )
        elif has_failed_stages:
            overall_status = WorkflowStatus.FAILED
            workflow_rationale = f"WORKFLOW FAILED: Halted due to stage failure in '{first_failed_stage}'."
        elif total_selected > 0:
            overall_status = WorkflowStatus.PARTIAL_SUCCESS if (research_ids or draft_ids) else WorkflowStatus.NO_CONTENT
            workflow_rationale = (
                f"WORKFLOW COMPLETED (NO PUBLISHABLE CONTENT): Processed {total_selected} topic(s), but zero "
                f"topics reached final publication ({blocked_publications} blocked/unpublishable)."
            )
        else:
            overall_status = WorkflowStatus.NO_CONTENT
            workflow_rationale = "WORKFLOW NO CONTENT: Zero topics selected for processing."

        completed_at = datetime.now(timezone.utc).isoformat()
        return _persist_result(
            AgentWorkflowResult(
                workflow_id=workflow_id,
                agent_id=agent_id,
                status=overall_status,
                started_at=started_at,
                completed_at=completed_at,
                stages=stages,
                selected_topic_ids=selected_topic_ids,
                research_ids=research_ids,
                draft_ids=draft_ids,
                publication_ids=publication_ids,
                is_successful=(overall_status in (WorkflowStatus.SUCCESS, WorkflowStatus.PARTIAL_SUCCESS, WorkflowStatus.NO_CONTENT)),
                halted_at_stage=first_failed_stage,
                rationale=workflow_rationale,
                traceability=traceability,
            )
        )
    except Exception as top_exc:
        s_end = datetime.now(timezone.utc).isoformat()
        logger.error(f"Unexpected top-level workflow failure for workflow '{workflow_id}': {top_exc}")
        halted = stages[-1].stage_name if stages else "workflow_initialization"
        failed_result = AgentWorkflowResult(
            workflow_id=workflow_id,
            agent_id=agent_id,
            status=WorkflowStatus.FAILED,
            started_at=started_at,
            completed_at=s_end,
            stages=stages,
            selected_topic_ids=selected_topic_ids,
            research_ids=research_ids,
            draft_ids=draft_ids,
            publication_ids=publication_ids,
            is_successful=False,
            halted_at_stage=halted,
            rationale=f"Workflow halted due to unexpected error: {type(top_exc).__name__}",
            traceability=traceability,
        )
        _persist_result(failed_result)
        return failed_result
